import json
import os
import queue
import re
import threading
import time
import tkinter as tk
import zlib
from datetime import datetime
from tkinter import messagebox, simpledialog, ttk

import cv2
import numpy as np
import serial
from PIL import Image, ImageTk
from pyzbar.pyzbar import ZBarSymbol, decode

# ----------------------------- Configuración -----------------------------
PORT_ESP = "COM7"       # ESP32-CAM (video) - ajusta al puerto que muestre Windows
PORT_ARDUINO = "COM8"   # Arduino (actuadores)
BAUD_ESP = 460800       # DEBE coincidir con Serial.begin() del sketch de la ESP32
BAUD_ARDUINO = 9600

MAGIC = b"\xAA\x55\xAA\x55"   # Cabecera propia de cada frame (no puede confundirse con el JPEG)
MAX_JPG = 250_000             # Tamaño máximo razonable de un JPEG VGA
COOLDOWN_QR = 3.0             # Segundos de pausa tras cerrar un diálogo
COOLDOWN_MISMO_QR = 6.0       # Segundos antes de volver a aceptar el MISMO QR

ARCHIVO_JSON = "computadoras.json"
ARCHIVO_HISTORIAL = "historial_prestamos.json"
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

TEMAS = {
    "oscuro": dict(bg="#1b1d23", panel="#262932", entry="#313541", fg="#e8eaf0",
                   muted="#8b90a0", accent="#4c8dff", border="#3a3f4d",
                   libre="#3ddc84", ocupada="#ff6b6b", btn="#343845"),
    "claro": dict(bg="#eef1f6", panel="#ffffff", entry="#ffffff", fg="#1f2430",
                  muted="#6b7280", accent="#2563eb", border="#cfd6e2",
                  libre="#15803d", ocupada="#dc2626", btn="#dde3ee"),
}


# ----------------------------- Utilidades de datos -----------------------------
def cargar_json(ruta, defecto):
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return defecto
    return defecto


def guardar_json(ruta, datos):
    """Escritura atómica: si el programa se cierra a mitad, el JSON no queda corrupto."""
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)
    os.replace(tmp, ruta)


def pc_vacia(pc_id, qr=""):
    return {"id": pc_id, "qr": qr, "estado": "Disponible", "persona": "",
            "docente": "", "materia": "", "dia": "", "horario": "", "fecha": ""}


def normalizar_id(texto):
    """'5' -> 'PC-05', 'pc-7' -> 'PC-07', otro texto -> en mayúsculas."""
    t = texto.strip().upper()
    m = re.fullmatch(r"(?:PC[-\s]*)?(\d+)", t)
    if m:
        return f"PC-{int(m.group(1)):02d}"
    return t


def extraer_jpgs(buf: bytearray, stats: dict):
    """
    Formato de frame: MAGIC(4) + longitud uint32 LE (4) + CRC32 uint32 LE (4) + JPEG.
    Los frames con CRC incorrecto (bytes perdidos/corruptos) se DESCARTAN.
    """
    jpgs = []
    while True:
        i = buf.find(MAGIC)
        if i < 0:
            if len(buf) > 3:
                del buf[:-3]
            break
        if i > 0:
            del buf[:i]
        if len(buf) < 12:
            break
        n = int.from_bytes(buf[4:8], "little")
        crc = int.from_bytes(buf[8:12], "little")
        if n < 100 or n > MAX_JPG:
            del buf[:4]
            continue
        if len(buf) < 12 + n:
            break
        jpg = bytes(buf[12:12 + n])
        if zlib.crc32(jpg) == crc and jpg[:2] == b"\xff\xd8":
            jpgs.append(jpg)
            stats["ok"] += 1
            del buf[:12 + n]
        else:
            stats["malos"] += 1
            del buf[:4]   # frame dañado: resincronizar en la siguiente cabecera
    return jpgs


class GestorIntegralApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Automatizado - ESP32-CAM & Arduino Gestor de PCs")
        self.root.geometry("1150x720")
        self.root.minsize(1000, 640)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.ser_esp = None
        self.ser_arduino = None
        self.conectado_esp = False
        self.conectado_arduino = False

        self.linterna_encendida = False
        self.modo_oscuro = True
        self.hilo_activo = True

        self.stats = {"ok": 0, "malos": 0}

        # Comunicación segura hilo de video -> hilo principal (Tkinter NO es thread-safe)
        self.frame_lock = threading.Lock()
        self.frame_nuevo = None
        self.cola_qr = queue.Queue()

        # Control de escaneo
        self.escaneando_lock = threading.Lock()
        self.dialogo_abierto = False
        self.bloqueo_hasta = 0.0
        self.ultimo_qr = ""
        self.ultimo_qr_t = 0.0

        # Estado del formulario / autoguardado
        self.pc_actual = None
        self._cargando = False
        self._after_id = None
        self.ventana_ayuda = None

        self.pcs = cargar_json(ARCHIVO_JSON, [])
        for pc in self.pcs:
            for k, v in pc_vacia("").items():
                pc.setdefault(k, v)
        if not self.pcs:
            self.pcs = [pc_vacia("PC-01"), pc_vacia("PC-02")]
            guardar_json(ARCHIVO_JSON, self.pcs)

        print("[DEBUG] Conectando dispositivos seriales...")
        self.conectar_dispositivos()

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.crear_widgets()
        self.aplicar_tema()

        print("[DEBUG] Iniciando hilo de video de la ESP32-CAM...")
        self.hilo_video = threading.Thread(target=self.lector_serial_esp_dedicado, daemon=True)
        self.hilo_video.start()

        self.loop_video()
        self.actualizar_interfaz()

    # ------------------------------- Puertos Seriales -------------------------------
    def abrir_esp(self):
        """Abre la ESP32-CAM con DTR/RTS en bajo ANTES de abrir, para no resetearla."""
        ser = serial.Serial()
        ser.port = PORT_ESP
        ser.baudrate = BAUD_ESP
        ser.timeout = 0.1
        ser.write_timeout = 1
        ser.dsrdtr = False
        ser.rtscts = False
        ser.dtr = False
        ser.rts = False
        ser.open()
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        return ser

    def abrir_arduino(self):
        ser = serial.Serial(PORT_ARDUINO, BAUD_ARDUINO, timeout=0.1, write_timeout=1)
        time.sleep(2)  # El Arduino se reinicia al abrir el puerto; hay que esperarlo
        ser.reset_input_buffer()
        return ser

    def conectar_dispositivos(self):
        try:
            self.ser_esp = self.abrir_esp()
            self.conectado_esp = True
            print(f"[DEBUG] ¡ESP32-CAM conectada en {PORT_ESP}!")
        except Exception as e:
            self.conectado_esp = False
            self.ser_esp = None
            print(f"[ERROR] No se pudo abrir el puerto ESP32 ({PORT_ESP}): {e}")

        try:
            self.ser_arduino = self.abrir_arduino()
            self.conectado_arduino = True
            print(f"[DEBUG] ¡Arduino conectado en {PORT_ARDUINO}!")
        except Exception as e:
            self.conectado_arduino = False
            self.ser_arduino = None
            print(f"[ERROR] No se pudo abrir el puerto Arduino ({PORT_ARDUINO}): {e}")

    def enviar_comando_arduino(self, comando: bytes):
        """Envía una señal al Arduino (reconecta si hace falta)."""
        if not self.conectado_arduino or self.ser_arduino is None:
            try:
                self.ser_arduino = self.abrir_arduino()
                self.conectado_arduino = True
            except Exception as e:
                self.conectado_arduino = False
                self.ser_arduino = None
                print(f"[ERROR] No se pudo reconectar al Arduino: {e}")
                return
        try:
            self.ser_arduino.write(comando)
            self.ser_arduino.flush()
            print(f"[DEBUG] Comando enviado al Arduino: {comando}")
        except Exception as e:
            print(f"[ERROR] Falló el envío al Arduino: {e}")
            self.conectado_arduino = False
            try:
                self.ser_arduino.close()
            except Exception:
                pass
            self.ser_arduino = None

    # ------------------------------- Widgets -------------------------------
    def crear_widgets(self):
        self.frame_top = ttk.Frame(self.root, padding=(15, 8))
        self.frame_top.pack(fill=tk.X)
        self.lbl_titulo = ttk.Label(self.frame_top, text="Panel Automatizado - ESP32-CAM & Arduino",
                                    font=("Segoe UI", 16, "bold"))
        self.lbl_titulo.pack(side=tk.LEFT)
        self.btn_tema = ttk.Button(self.frame_top, text="☀️ Modo Claro", command=self.cambiar_tema)
        self.btn_tema.pack(side=tk.RIGHT, padx=5)
        self.btn_ayuda = ttk.Button(self.frame_top, text="❓ Ayuda", command=self.mostrar_ayuda)
        self.btn_ayuda.pack(side=tk.RIGHT, padx=5)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tab_camara = ttk.Frame(self.notebook, padding=10)
        self.tab_gestion = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_camara, text="  📷 Escáner QR & ESP32-CAM  ")
        self.notebook.add(self.tab_gestion, text="  💻 Gestor e Inventario de PCs  ")

        self._crear_tab_camara()
        self._crear_tab_gestion()
        self.refrescar_tablas()

    def _crear_tab_camara(self):
        self.frame_video_container = ttk.Frame(self.tab_camara, relief=tk.GROOVE, borderwidth=2)
        self.frame_video_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # Evita el bucle "la imagen agranda el contenedor -> la imagen se agranda..."
        self.frame_video_container.pack_propagate(False)
        self.lbl_video = ttk.Label(self.frame_video_container, anchor="center")
        self.lbl_video.pack(fill=tk.BOTH, expand=True)

        panel = ttk.Frame(self.tab_camara, padding=(15, 0))
        panel.pack(side=tk.RIGHT, fill=tk.Y)

        self.btn_linterna = tk.Button(panel, text="🔦 Linterna ESP32: APAGADA",
                                      font=("Segoe UI", 10, "bold"), command=self.toggle_linterna,
                                      height=2, width=26, relief=tk.FLAT, cursor="hand2")
        self.btn_linterna.pack(pady=15)

        self.btn_puerta = tk.Button(panel, text="🚪 Abrir puerta", bg="#17a2b8", fg="white",
                                    font=("Segoe UI", 10, "bold"), command=self.abrir_puerta,
                                    height=2, width=26, relief=tk.FLAT, cursor="hand2")
        self.btn_puerta.pack(pady=(0, 10))

        ttk.Label(panel, text="Último QR escaneado:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=5)
        self.txt_qr = tk.Text(panel, height=6, width=30, font=("Consolas", 10), relief=tk.FLAT,
                              wrap="word")
        self.txt_qr.pack(fill=tk.X, pady=5)
        self.txt_qr.insert(tk.END, "Esperando escaneo...")
        self.txt_qr.config(state=tk.DISABLED)

        ttk.Label(panel, text="Acerca el código QR de la PC a la ESP32-CAM.\n"
                              "El Arduino reaccionará de forma automática.",
                  justify="left", font=("Segoe UI", 9)).pack(anchor="w", pady=10)

        self.lbl_estado = ttk.Label(panel, text="Estado: Conectando...", font=("Segoe UI", 9, "italic"))
        self.lbl_estado.pack(side=tk.BOTTOM, pady=10)

    def _crear_tab_gestion(self):
        self.var_id = tk.StringVar()
        self.var_persona = tk.StringVar()
        self.var_docente = tk.StringVar()
        self.var_materia = tk.StringVar()
        self.var_dia = tk.StringVar()
        self.var_horario = tk.StringVar()
        for v in (self.var_persona, self.var_docente, self.var_materia,
                  self.var_dia, self.var_horario):
            v.trace_add("write", self._on_cambio)

        f_form = ttk.LabelFrame(self.tab_gestion, text=" Datos del préstamo ", padding=12)
        f_form.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.lbl_sel = ttk.Label(f_form, text="Ninguna PC seleccionada", font=("Segoe UI", 11, "bold"))
        self.lbl_sel.pack(anchor="w", pady=(0, 2))
        self.lbl_qr = ttk.Label(f_form, text="", font=("Segoe UI", 8))
        self.lbl_qr.pack(anchor="w", pady=(0, 8))

        def campo(texto, var, readonly=False):
            ttk.Label(f_form, text=texto).pack(anchor="w", pady=(4, 0))
            e = ttk.Entry(f_form, textvariable=var, width=28, font=("Segoe UI", 10),
                          state="readonly" if readonly else "normal")
            e.pack(pady=2)
            return e

        campo("ID de PC:", self.var_id, readonly=True)
        self.ent_persona = campo("Estudiante / Persona que la lleva:", self.var_persona)
        self.ent_docente = campo("Docente a cargo:", self.var_docente)
        self.ent_materia = campo("Materia:", self.var_materia)

        ttk.Label(f_form, text="Día (automático, editable):").pack(anchor="w", pady=(4, 0))
        self.combo_dia = ttk.Combobox(f_form, textvariable=self.var_dia, values=DIAS,
                                      state="readonly", width=26)
        self.combo_dia.pack(pady=2)

        campo("Horario (inicia automático):", self.var_horario)

        self.lbl_guardado = ttk.Label(f_form, text="💾 Guardado automático activo",
                                      font=("Segoe UI", 8, "italic"))
        self.lbl_guardado.pack(anchor="w", pady=(10, 4))

        def boton(texto, color, cmd):
            b = tk.Button(f_form, text=texto, bg=color, fg="white", font=("Segoe UI", 9, "bold"),
                          relief=tk.FLAT, width=28, pady=4, cursor="hand2", command=cmd)
            b.pack(pady=3)
            return b

        boton("➕ Agregar PC manualmente", "#17a2b8", self.agregar_pc_manual)
        boton("🔄 Devolver / Liberar PC", "#e0a800", self.devolver_seleccionada)
        boton("🗑️ Eliminar del inventario", "#dc3545", self.eliminar_pc)
        boton("✖ Limpiar selección", "#6c757d", self.deseleccionar)

        f_tablas = ttk.Frame(self.tab_gestion)
        f_tablas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.lbl_disp = ttk.Label(f_tablas, text="Computadoras disponibles", font=("Segoe UI", 10, "bold"))
        self.lbl_disp.pack(anchor="w")
        self.tree_disp = ttk.Treeview(f_tablas, columns=("ID", "Estado"), show="headings", height=6)
        self.tree_disp.heading("ID", text="ID de PC")
        self.tree_disp.heading("Estado", text="Estado")
        self.tree_disp.pack(fill=tk.BOTH, expand=True, pady=3)
        self.tree_disp.bind("<<TreeviewSelect>>", self.on_seleccion_tabla)

        self.lbl_usadas = ttk.Label(f_tablas, text="Computadoras en préstamo", font=("Segoe UI", 10, "bold"))
        self.lbl_usadas.pack(anchor="w", pady=(8, 0))
        cols = ("ID", "Persona", "Docente", "Materia", "Día", "Horario")
        self.tree_usadas = ttk.Treeview(f_tablas, columns=cols, show="headings", height=8)
        for c in cols:
            self.tree_usadas.heading(c, text=c)
            self.tree_usadas.column(c, width=90 if c in ("ID", "Día") else 120)
        self.tree_usadas.pack(fill=tk.BOTH, expand=True, pady=3)
        self.tree_usadas.bind("<<TreeviewSelect>>", self.on_seleccion_tabla)

    # ------------------------------- Tema -------------------------------
    def cambiar_tema(self):
        self.modo_oscuro = not self.modo_oscuro
        self.aplicar_tema()

    def aplicar_tema(self):
        p = TEMAS["oscuro" if self.modo_oscuro else "claro"]
        self.p = p
        s = self.style
        self.root.config(bg=p["bg"])

        s.configure(".", background=p["bg"], foreground=p["fg"], fieldbackground=p["entry"],
                    bordercolor=p["border"], lightcolor=p["bg"], darkcolor=p["bg"],
                    troughcolor=p["panel"], focuscolor=p["accent"])
        s.configure("TFrame", background=p["bg"])
        s.configure("TLabel", background=p["bg"], foreground=p["fg"])
        s.configure("TLabelframe", background=p["bg"], bordercolor=p["border"])
        s.configure("TLabelframe.Label", background=p["bg"], foreground=p["accent"],
                    font=("Segoe UI", 10, "bold"))
        s.configure("TNotebook", background=p["bg"], bordercolor=p["border"])
        s.configure("TNotebook.Tab", background=p["btn"], foreground=p["fg"], padding=(14, 7),
                    font=("Segoe UI", 10, "bold"))
        s.map("TNotebook.Tab", background=[("selected", p["accent"])],
              foreground=[("selected", "#ffffff")])
        s.configure("TButton", background=p["btn"], foreground=p["fg"], padding=(10, 5),
                    font=("Segoe UI", 9, "bold"), borderwidth=0)
        s.map("TButton", background=[("active", p["accent"])], foreground=[("active", "#ffffff")])
        s.configure("TEntry", fieldbackground=p["entry"], foreground=p["fg"], insertcolor=p["fg"])
        s.map("TEntry", fieldbackground=[("readonly", p["panel"])])
        s.configure("TCombobox", fieldbackground=p["entry"], background=p["btn"],
                    foreground=p["fg"], arrowcolor=p["fg"])
        s.map("TCombobox", fieldbackground=[("readonly", p["entry"])],
              foreground=[("readonly", p["fg"])])
        s.configure("Treeview", background=p["panel"], fieldbackground=p["panel"],
                    foreground=p["fg"], rowheight=26, borderwidth=0)
        s.map("Treeview", background=[("selected", p["accent"])],
              foreground=[("selected", "#ffffff")])
        s.configure("Treeview.Heading", background=p["btn"], foreground=p["fg"],
                    font=("Segoe UI", 9, "bold"), relief="flat")
        s.map("Treeview.Heading", background=[("active", p["accent"])])

        self.root.option_add("*TCombobox*Listbox.background", p["entry"])
        self.root.option_add("*TCombobox*Listbox.foreground", p["fg"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", p["accent"])

        for tree in (self.tree_disp, self.tree_usadas):
            tree.tag_configure("libre", foreground=p["libre"])
            tree.tag_configure("ocupada", foreground=p["ocupada"])

        self.txt_qr.config(bg=p["panel"], fg=p["fg"], insertbackground=p["fg"])
        self.lbl_qr.config(foreground=p["muted"])
        self.lbl_guardado.config(foreground=p["muted"])
        self.btn_tema.config(text="☀️ Modo Claro" if self.modo_oscuro else "🌙 Modo Oscuro")
        self._actualizar_boton_linterna()

    # ------------------------------- Ayuda -------------------------------
    def mostrar_ayuda(self):
        if self.ventana_ayuda and self.ventana_ayuda.winfo_exists():
            self.ventana_ayuda.lift()
            return
        p = self.p
        win = tk.Toplevel(self.root)
        self.ventana_ayuda = win
        win.title("Ayuda e Instrucciones")
        win.geometry("640x560")
        win.config(bg=p["bg"])

        txt = tk.Text(win, wrap="word", bg=p["panel"], fg=p["fg"], relief=tk.FLAT,
                      font=("Segoe UI", 10), padx=18, pady=14, spacing3=4)
        sb = ttk.Scrollbar(win, command=txt.yview)
        txt.config(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.tag_configure("h", font=("Segoe UI", 12, "bold"), foreground=p["accent"], spacing1=10)

        secciones = [
            ("🚀 Conexión Dual (ESP32-CAM + Arduino)", [
                f"• ESP32-CAM ({PORT_ESP}): Transmite el video y detecta los códigos QR.",
                f"• Arduino ({PORT_ARDUINO}): Recibe las órdenes automáticas al prestar o devolver PCs.",
            ]),
            ("📷 Escaneo de QR", [
                "• Acerca el QR a 10-20 cm de la cámara, bien iluminado y sin reflejos.",
                "• Si hay poca luz, enciende la linterna de la ESP32.",
                "• Un QR nuevo te pedirá el ID de la PC para vincularlo.",
                "• El mismo QR no se vuelve a procesar durante unos segundos.",
            ]),
            ("💻 Gestión de préstamos", [
                "• Al escribir el nombre de la persona, la PC pasa a 'Ocupada' automáticamente.",
                "• 'Devolver / Liberar' la deja disponible y guarda el registro en el historial.",
                "• Todos los cambios se guardan solos.",
            ]),
        ]
        for titulo, lineas in secciones:
            txt.insert(tk.END, titulo + "\n", "h")
            for l in lineas:
                txt.insert(tk.END, l + "\n")
        txt.config(state=tk.DISABLED)

    # ------------------------------- Linterna ESP32 -------------------------------
    def _actualizar_boton_linterna(self):
        if self.linterna_encendida:
            self.btn_linterna.config(text="🔦 Linterna ESP32: ENCENDIDA", bg="#28a745", fg="white",
                                     activebackground="#28a745")
        else:
            self.btn_linterna.config(text="🔦 Linterna ESP32: APAGADA", bg=self.p["btn"],
                                     fg=self.p["fg"], activebackground=self.p["accent"])

    def toggle_linterna(self):
        ser = self.ser_esp
        if not self.conectado_esp or ser is None:
            messagebox.showerror("Error", f"No hay conexión con la ESP32-CAM en {PORT_ESP}.",
                                 parent=self.root)
            return
        nuevo = not self.linterna_encendida
        try:
            ser.write(b"1" if nuevo else b"0")
        except Exception as e:
            self.conectado_esp = False
            messagebox.showerror("Error", f"No se pudo enviar el comando: {e}", parent=self.root)
            return
        self.linterna_encendida = nuevo
        self._actualizar_boton_linterna()

    # ------------------------------- Puerta (servo del Arduino) -------------------------------
    def abrir_puerta(self):
        """Abre la puerta manualmente (comando 'O'); se cierra sola tras unos segundos."""
        self.enviar_comando_arduino(b"O")
        if not self.conectado_arduino:
            messagebox.showerror("Error", f"No hay conexión con el Arduino en {PORT_ARDUINO}.",
                                 parent=self.root)

    # ------------------------------- Hilo de Video Serial (ESP32-CAM) -------------------------------
    def lector_serial_esp_dedicado(self):
        """
        Hilo SOLO de lectura/decodificación. No toca ningún widget de Tkinter:
        deja el último frame en self.frame_nuevo y los QR en self.cola_qr.
        """
        buf = bytearray()
        detector_cv = cv2.QRCodeDetector()

        while self.hilo_activo:
            if not self.conectado_esp or self.ser_esp is None:
                try:
                    self.ser_esp = self.abrir_esp()
                    self.conectado_esp = True
                    buf.clear()
                    print(f"[DEBUG] ESP32-CAM reconectada en {PORT_ESP}")
                except Exception:
                    self.conectado_esp = False
                    self.ser_esp = None
                    time.sleep(1)
                continue

            try:
                ser = self.ser_esp
                data = ser.read(max(1, ser.in_waiting))
                if data:
                    buf.extend(data)
                if len(buf) > 2_000_000:   # seguridad ante basura continua
                    buf.clear()

                jpgs = extraer_jpgs(buf, self.stats)
                if not jpgs:
                    continue

                # Si nos atrasamos, solo procesamos el frame MÁS RECIENTE
                frame = cv2.imdecode(np.frombuffer(jpgs[-1], np.uint8), cv2.IMREAD_COLOR)
                if frame is None:
                    continue

                self._escanear_qr(frame, detector_cv)

                with self.frame_lock:
                    self.frame_nuevo = frame

            except (serial.SerialException, OSError) as e:
                print(f"[ERROR] Puerto ESP32 desconectado: {e}")
                self.conectado_esp = False
                try:
                    self.ser_esp.close()
                except Exception:
                    pass
                self.ser_esp = None
                time.sleep(1)
            except Exception as e:
                print(f"[ERROR] Hilo de video: {e}")
                time.sleep(0.05)

    def _escanear_qr(self, frame, detector_cv):
        with self.escaneando_lock:
            if self.dialogo_abierto or time.time() < self.bloqueo_hasta:
                return

        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            qr_str, poly = None, None

            # Intento 1 y 2: pyzbar (solo QR) sobre gris normal y con contraste mejorado
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            for img in (gray, clahe.apply(gray)):
                resultados = decode(img, symbols=[ZBarSymbol.QRCODE])
                if resultados:
                    obj = resultados[0]
                    qr_str = obj.data.decode("utf-8", errors="ignore").strip()
                    poly = [(p.x, p.y) for p in obj.polygon]
                    break

            # Intento 3: detector QR de OpenCV como respaldo
            if not qr_str:
                txt, pts, _ = detector_cv.detectAndDecode(gray)
                if txt:
                    qr_str = txt.strip()
                    if pts is not None:
                        poly = pts.reshape(-1, 2).astype(int).tolist()

            if not qr_str:
                return

            if poly and len(poly) >= 3:
                cv2.polylines(frame, [np.array(poly, np.int32)], True, (0, 255, 0), 3)

            if qr_str == self.ultimo_qr and time.time() - self.ultimo_qr_t < COOLDOWN_MISMO_QR:
                return

            with self.escaneando_lock:
                if self.dialogo_abierto:
                    return
                self.dialogo_abierto = True
            self.cola_qr.put(qr_str)
        except Exception:
            # Cualquier fallo de decodificación se ignora; el video sigue
            pass

    # ------------------------------- Bucle de video (hilo principal) -------------------------------
    def loop_video(self):
        if not self.hilo_activo:
            return
        self.root.after(40, self.loop_video)   # re-programar primero, por si hay diálogos modales

        try:
            with self.frame_lock:
                frame = self.frame_nuevo
                self.frame_nuevo = None

            if frame is not None:
                w = self.frame_video_container.winfo_width()
                h = self.frame_video_container.winfo_height()
                fh, fw = frame.shape[:2]
                if w > 20 and h > 20:
                    ratio = min(w / fw, h / fh)
                    frame = cv2.resize(frame, (max(1, int(fw * ratio)), max(1, int(fh * ratio))),
                                       interpolation=cv2.INTER_LINEAR)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                imgtk = ImageTk.PhotoImage(Image.fromarray(rgb))
                self.lbl_video.imgtk = imgtk      # evita que el recolector la borre
                self.lbl_video.configure(image=imgtk)

            try:
                qr = self.cola_qr.get_nowait()
            except queue.Empty:
                qr = None
            if qr:
                # after() para salir de este callback antes de abrir diálogos modales
                self.root.after(10, lambda d=qr: self.procesar_qr_automatico(d))
        except Exception as e:
            print(f"[ERROR] loop_video: {e}")

    # ------------------------------- Lógica de PCs -------------------------------
    def buscar_por_id(self, pc_id):
        return next((pc for pc in self.pcs if pc["id"] == pc_id), None)

    def buscar_por_qr(self, qr):
        for pc in self.pcs:
            if pc.get("qr") and pc["qr"] == qr:
                return pc
        return self.buscar_por_id(qr.strip().upper())

    def siguiente_id(self):
        nums = [int(m.group(1)) for pc in self.pcs
                if (m := re.fullmatch(r"PC-(\d+)", pc["id"]))]
        return f"PC-{(max(nums) if nums else 0) + 1:02d}"

    def guardar_todo(self):
        guardar_json(ARCHIVO_JSON, self.pcs)
        self.lbl_guardado.config(text=f"💾 Guardado automático ✔ {datetime.now():%H:%M:%S}")

    def procesar_qr_automatico(self, qr_data):
        """Se ejecuta siempre en el hilo principal de Tkinter."""
        try:
            self.txt_qr.config(state=tk.NORMAL)
            self.txt_qr.delete("1.0", tk.END)
            self.txt_qr.insert(tk.END, f"¡Escaneado!\n{qr_data}")
            self.txt_qr.config(state=tk.DISABLED)

            self.flush_autoguardado()
            self.notebook.select(self.tab_gestion)
            self.root.lift()

            pc = self.buscar_por_qr(qr_data)

            if pc is None:
                m = re.fullmatch(r"PC[-\s]*\d+", qr_data.strip().upper())
                sugerido = normalizar_id(qr_data) if m else self.siguiente_id()
                if self.buscar_por_id(sugerido):
                    sugerido = self.siguiente_id()
                entrada = simpledialog.askstring(
                    "Nueva PC detectada",
                    "Este QR no está registrado.\nIngresa el ID de la PC:",
                    initialvalue=sugerido, parent=self.root)
                if not entrada or not entrada.strip():
                    return
                pc_id = normalizar_id(entrada)
                existente = self.buscar_por_id(pc_id)
                if existente:
                    if existente.get("qr") and existente["qr"] != qr_data:
                        messagebox.showerror("Error", f"{pc_id} ya tiene otro QR vinculado.",
                                             parent=self.root)
                        return
                    existente["qr"] = qr_data
                    pc = existente
                else:
                    pc = pc_vacia(pc_id, qr_data)
                    self.pcs.append(pc)
                self.guardar_todo()
                self.refrescar_tablas()

            self.cargar_pc(pc)

            if pc["estado"] == "Disponible":
                if messagebox.askyesno("PC disponible",
                                       f"La {pc['id']} está disponible.\n¿Deseas prestarla?",
                                       parent=self.root):
                    self.enviar_comando_arduino(b"A")
                    self.ent_persona.focus_set()
                else:
                    self.deseleccionar()
            else:
                if messagebox.askyesno(
                        "PC en préstamo",
                        f"La {pc['id']} está prestada a '{pc['persona']}'.\n"
                        "¿Deseas DEVOLVERLA y dejarla disponible?",
                        parent=self.root):
                    self.enviar_comando_arduino(b"D")
                    self.devolver(pc["id"])
        except Exception as e:
            print(f"[ERROR] Procesando QR: {e}")
        finally:
            with self.escaneando_lock:
                self.ultimo_qr = qr_data
                self.ultimo_qr_t = time.time()
                self.bloqueo_hasta = time.time() + COOLDOWN_QR
                self.dialogo_abierto = False

    def agregar_pc_manual(self):
        entrada = simpledialog.askstring("Agregar PC", "ID de la nueva PC:",
                                         initialvalue=self.siguiente_id(), parent=self.root)
        if not entrada or not entrada.strip():
            return
        pc_id = normalizar_id(entrada)
        if self.buscar_por_id(pc_id):
            messagebox.showerror("Error", f"La computadora {pc_id} ya existe.", parent=self.root)
            return
        pc = pc_vacia(pc_id)
        self.pcs.append(pc)
        self.guardar_todo()
        self.refrescar_tablas()
        self.cargar_pc(pc)

    def devolver_seleccionada(self):
        if not self.pc_actual:
            messagebox.showwarning("Aviso", "Selecciona o escanea una PC primero.", parent=self.root)
            return
        pc = self.buscar_por_id(self.pc_actual)
        if pc and pc["estado"] == "Disponible":
            messagebox.showinfo("Información", f"{pc['id']} ya está disponible.", parent=self.root)
            return
        if messagebox.askyesno("Confirmar", f"¿Devolver {self.pc_actual}?", parent=self.root):
            self.enviar_comando_arduino(b"D")
            self.devolver(self.pc_actual)

    def devolver(self, pc_id):
        pc = self.buscar_por_id(pc_id)
        if not pc:
            return
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        if pc["estado"] == "Ocupada":
            hist = cargar_json(ARCHIVO_HISTORIAL, [])
            hist.append({**{k: pc[k] for k in ("id", "persona", "docente", "materia",
                                               "dia", "horario", "fecha")},
                         "devuelta": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            guardar_json(ARCHIVO_HISTORIAL, hist)
        qr = pc.get("qr", "")
        pc.update(pc_vacia(pc_id, qr))
        self.guardar_todo()
        self.deseleccionar()
        self.refrescar_tablas()

    def eliminar_pc(self):
        if not self.pc_actual:
            messagebox.showwarning("Aviso", "Selecciona o escanea la PC a eliminar.", parent=self.root)
            return
        if messagebox.askyesno("Confirmar", f"¿Eliminar permanentemente la {self.pc_actual}?",
                               parent=self.root):
            self.pcs = [pc for pc in self.pcs if pc["id"] != self.pc_actual]
            if self._after_id:
                self.root.after_cancel(self._after_id)
                self._after_id = None
            self.guardar_todo()
            self.deseleccionar()
            self.refrescar_tablas()

    # ------------------------------- Formulario y autoguardado -------------------------------
    def cargar_pc(self, pc):
        self._cargando = True
        ahora = datetime.now()
        self.pc_actual = pc["id"]
        self.var_id.set(pc["id"])
        self.var_persona.set(pc["persona"])
        self.var_docente.set(pc["docente"])
        self.var_materia.set(pc["materia"])
        self.var_dia.set(pc["dia"] or DIAS[ahora.weekday()])
        self.var_horario.set(pc["horario"] or f"{ahora:%H:%M} - ")
        self.lbl_sel.config(text=f"{pc['id']} · {pc['estado']}")
        qr = pc.get("qr", "")
        self.lbl_qr.config(text=("QR: " + (qr[:38] + "…" if len(qr) > 38 else qr)) if qr
                           else "Sin QR vinculado")
        self.refrescar_tablas()
        self._cargando = False

    def deseleccionar(self):
        self._cargando = True
        self.pc_actual = None
        for v in (self.var_id, self.var_persona, self.var_docente, self.var_materia,
                  self.var_dia, self.var_horario):
            v.set("")
        self.lbl_sel.config(text="Ninguna PC seleccionada")
        self.lbl_qr.config(text="")
        for t in (self.tree_disp, self.tree_usadas):
            t.selection_remove(t.selection())
        self._cargando = False

    def _on_cambio(self, *_):
        if self._cargando or not self.pc_actual:
            return
        if self._after_id:
            self.root.after_cancel(self._after_id)
        self._after_id = self.root.after(500, self.autoguardar)

    def flush_autoguardado(self):
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
            self.autoguardar()

    def autoguardar(self):
        self._after_id = None
        pc = self.buscar_por_id(self.pc_actual) if self.pc_actual else None
        if not pc:
            return
        persona = self.var_persona.get().strip()
        if persona:
            if pc["estado"] != "Ocupada":
                pc["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pc.update(estado="Ocupada", persona=persona,
                      docente=self.var_docente.get().strip(),
                      materia=self.var_materia.get().strip(),
                      dia=self.var_dia.get(), horario=self.var_horario.get().strip())
        elif pc["estado"] == "Ocupada":
            # Se borró el nombre de una PC prestada: vuelve a disponible
            qr = pc.get("qr", "")
            pc.update(pc_vacia(pc["id"], qr))
        else:
            return  # PC disponible sin persona: no hay nada que guardar
        self.guardar_todo()
        self.lbl_sel.config(text=f"{pc['id']} · {pc['estado']}")
        self.refrescar_tablas()

    # ------------------------------- Tablas -------------------------------
    def refrescar_tablas(self):
        sel = self.pc_actual
        previo = self._cargando
        self._cargando = True
        for t in (self.tree_disp, self.tree_usadas):
            t.delete(*t.get_children())

        libres = [pc for pc in self.pcs if pc["estado"] == "Disponible"]
        usadas = [pc for pc in self.pcs if pc["estado"] == "Ocupada"]

        for pc in libres:
            item_id = self.tree_disp.insert("", tk.END, values=(pc["id"], pc["estado"]), tags=("libre",))
            if pc["id"] == sel:
                self.tree_disp.selection_set(item_id)

        for pc in usadas:
            item_id = self.tree_usadas.insert("", tk.END, values=(
                pc["id"], pc["persona"], pc["docente"], pc["materia"], pc["dia"], pc["horario"]
            ), tags=("ocupada",))
            if pc["id"] == sel:
                self.tree_usadas.selection_set(item_id)

        self._cargando = previo

    def on_seleccion_tabla(self, event):
        # Los eventos <<TreeviewSelect>> se entregan DESPUÉS de selection_set(), cuando
        # _cargando ya es False. Por eso se compara con la PC actual para evitar un bucle infinito.
        if self._cargando:
            return
        widget = event.widget
        sel = widget.selection()
        if not sel:
            return
        valores = widget.item(sel[0]).get("values")
        if not valores:
            return
        pc_id = str(valores[0])
        if pc_id == self.pc_actual:
            return

        otra = self.tree_usadas if widget == self.tree_disp else self.tree_disp
        if otra.selection():
            self._cargando = True
            otra.selection_remove(otra.selection())
            self._cargando = False

        self.flush_autoguardado()   # no perder lo que se estaba escribiendo
        pc = self.buscar_por_id(pc_id)
        if pc:
            self.cargar_pc(pc)

    def actualizar_interfaz(self):
        status_esp = f"ESP32 ({PORT_ESP}) OK" if self.conectado_esp else f"ESP32 ({PORT_ESP}) Sin conexión"
        status_ard = f"Arduino ({PORT_ARDUINO}) OK" if self.conectado_arduino else f"Arduino ({PORT_ARDUINO}) Sin conexión"
        self.lbl_estado.config(text=f"Estado: {status_esp} | {status_ard}\nFrames OK: {self.stats['ok']} | Dañados: {self.stats['malos']}")

        # Si la ESP32 se desconectó, la linterna ya no está encendida
        if not self.conectado_esp and self.linterna_encendida:
            self.linterna_encendida = False
            self._actualizar_boton_linterna()

        if self.hilo_activo:
            self.root.after(1000, self.actualizar_interfaz)

    # ------------------------------- Cierre -------------------------------
    def on_close(self):
        self.hilo_activo = False
        try:
            self.flush_autoguardado()
        except Exception:
            pass
        try:
            self.hilo_video.join(timeout=1.0)
        except Exception:
            pass
        for ser in (self.ser_esp, self.ser_arduino):
            try:
                if ser:
                    ser.close()
            except Exception:
                pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = GestorIntegralApp(root)
    root.mainloop()