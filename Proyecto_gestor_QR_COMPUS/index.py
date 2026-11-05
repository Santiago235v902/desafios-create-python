import json
import os
import re
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, simpledialog, ttk

import cv2
import numpy as np
import serial
from PIL import Image, ImageTk
from pyzbar.pyzbar import decode

PORT = "COM6"
BAUD = 460800
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
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)


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


class GestorIntegralApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Automatizado - ESP32-CAM & Gestor de PCs")
        self.root.geometry("1150x720")
        self.root.minsize(1000, 640)

        self.ser = None
        self.conectado = False
        self.linterna_encendida = False
        self.modo_oscuro = True
        self.hilo_activo = True
        self.frame_actual = None

        # Control de escaneo (permite re-escanear el mismo QR)
        self.dialogo_abierto = False
        self.bloqueo_hasta = 0.0

        # Estado del formulario / autoguardado
        self.pc_actual = None
        self._cargando = False
        self._after_id = None
        self.ventana_ayuda = None

        self.pcs = cargar_json(ARCHIVO_JSON, [])
        for pc in self.pcs:                      # migración de JSON antiguo
            for k, v in pc_vacia("").items():
                pc.setdefault(k, v)
        if not self.pcs:
            self.pcs = [pc_vacia("PC-01"), pc_vacia("PC-02")]
            guardar_json(ARCHIVO_JSON, self.pcs)

        print("[DEBUG] Iniciando conexión serial...")
        self.conectar_serial()

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.crear_widgets()
        self.aplicar_tema()

        print("[DEBUG] Iniciando hilo de video...")
        self.hilo_video = threading.Thread(target=self.lector_serial_dedicado, daemon=True)
        self.hilo_video.start()

        self.actualizar_interfaz()

    # ------------------------------- Serial -------------------------------
    def conectar_serial(self):
        try:
            self.ser = serial.Serial(PORT, BAUD, timeout=0.1, dsrdtr=False, rtscts=False)
            self.ser.dtr = False
            self.ser.rts = False
            self.ser.flushInput()
            self.ser.flushOutput()
            self.conectado = True
            print(f"[DEBUG] ¡Conectado exitosamente al puerto {PORT}!")
        except Exception as e:
            self.conectado = False
            print(f"[ERROR] No se pudo abrir el puerto {PORT}: {e}")

    # ------------------------------- Widgets -------------------------------
    def crear_widgets(self):
        # Barra superior
        self.frame_top = ttk.Frame(self.root, padding=(15, 8))
        self.frame_top.pack(fill=tk.X)
        self.lbl_titulo = ttk.Label(self.frame_top, text="Panel Automatizado de Préstamo con QR",
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
        self.notebook.add(self.tab_camara, text="  📷 Escáner QR & Cámara  ")
        self.notebook.add(self.tab_gestion, text="  💻 Gestor e Inventario de PCs  ")

        self._crear_tab_camara()
        self._crear_tab_gestion()
        self.refrescar_tablas()

    def _crear_tab_camara(self):
        self.frame_video_container = ttk.Frame(self.tab_camara, relief=tk.GROOVE, borderwidth=2)
        self.frame_video_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.lbl_video = ttk.Label(self.frame_video_container, anchor="center")
        self.lbl_video.pack(fill=tk.BOTH, expand=True)

        panel = ttk.Frame(self.tab_camara, padding=(15, 0))
        panel.pack(side=tk.RIGHT, fill=tk.Y)

        self.btn_linterna = tk.Button(panel, text="🔦 Linterna: APAGADA",
                                      font=("Segoe UI", 10, "bold"), command=self.toggle_linterna,
                                      height=2, width=24, relief=tk.FLAT, cursor="hand2")
        self.btn_linterna.pack(pady=15)

        ttk.Label(panel, text="Último QR escaneado:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=5)
        self.txt_qr = tk.Text(panel, height=6, width=30, font=("Consolas", 10), relief=tk.FLAT,
                              wrap="word")
        self.txt_qr.pack(fill=tk.X, pady=5)
        self.txt_qr.insert(tk.END, "Esperando escaneo...")
        self.txt_qr.config(state=tk.DISABLED)

        ttk.Label(panel, text="Acerca el código QR de la PC a la cámara.\n"
                              "Todo lo demás es automático.",
                  justify="left", font=("Segoe UI", 9)).pack(anchor="w", pady=10)

        self.lbl_estado = ttk.Label(panel, text="Estado: Conectando...", font=("Segoe UI", 9, "italic"))
        self.lbl_estado.pack(side=tk.BOTTOM, pady=10)

    def _crear_tab_gestion(self):
        # Variables del formulario (con autoguardado)
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

        # Tablas
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
        if not self.linterna_encendida:
            self.btn_linterna.config(bg=p["btn"], fg=p["fg"], activebackground=p["accent"])
        else:
            self.btn_linterna.config(bg="#28a745", fg="white")

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
            ("🚀 Cómo funciona (todo con el QR)", [
                "1. Acerca el QR de una PC a la cámara. El sistema lo detecta solo.",
                "2. Si el QR es nuevo, te pide el ID de la PC. Ya viene sugerido el siguiente "
                "(PC-03, PC-04...). Puedes aceptar o escribir otro (ej. '7' → PC-07). "
                "El enlace del QR queda vinculado a esa PC, pero nunca se usa como nombre.",
                "3. Se abre el Gestor con las tablas y los datos de esa PC.",
            ]),
            ("📋 Préstamo", [
                "• Si la PC está LIBRE te pregunta si deseas prestarla. Al decir Sí, completa "
                "estudiante, docente y materia. El día y la hora de inicio se rellenan solos.",
                "• Todo se guarda automáticamente mientras escribes. No hay botón de guardar.",
            ]),
            ("🔄 Devolución", [
                "• Vuelve a escanear el QR de una PC prestada: verás sus datos autorrellenados "
                "y te preguntará si deseas devolverla.",
                "• Al devolverla, todos sus campos quedan en blanco para el siguiente uso y "
                "se registra en 'historial_prestamos.json'.",
            ]),
            ("🧰 Botones", [
                "• 🔦 Linterna: enciende/apaga el LED de la ESP32-CAM (útil con poca luz).",
                "• ➕ Agregar PC manualmente: crea una PC sin QR (se numera sola).",
                "• 🔄 Devolver / Liberar: devuelve la PC seleccionada sin escanear.",
                "• 🗑️ Eliminar: borra la PC del inventario.",
                "• ✖ Limpiar selección: vacía el formulario.",
                "• ☀️/🌙: cambia entre modo claro y oscuro.",
                "• Haz clic en cualquier fila de las tablas para ver o editar sus datos.",
            ]),
            ("💡 Consejos", [
                "• Si no detecta el QR, enciende la linterna y acércalo ~10–20 cm.",
                "• Tras cada escaneo hay una pausa de 3 s para evitar lecturas repetidas.",
                "• Verde = disponible, rojo = en préstamo.",
            ]),
        ]
        for titulo, lineas in secciones:
            txt.insert(tk.END, titulo + "\n", "h")
            for l in lineas:
                txt.insert(tk.END, l + "\n")
        txt.config(state=tk.DISABLED)

    # ------------------------------- Linterna -------------------------------
    def toggle_linterna(self):
        if not self.conectado:
            self.conectar_serial()
        if not self.conectado:
            messagebox.showerror("Error", "No hay conexión serial con la ESP32-CAM.")
            return
        self.linterna_encendida = not self.linterna_encendida
        try:
            if self.linterna_encendida:
                self.ser.write(b"1")
                self.btn_linterna.config(text="🔦 Linterna: ENCENDIDA", bg="#28a745", fg="white")
            else:
                self.ser.write(b"0")
                self.btn_linterna.config(text="🔦 Linterna: APAGADA", bg=self.p["btn"], fg=self.p["fg"])
        except Exception:
            self.conectado = False

    # ------------------------------- Lógica de PCs -------------------------------
    def buscar_por_id(self, pc_id):
        return next((pc for pc in self.pcs if pc["id"] == pc_id), None)

    def buscar_por_qr(self, qr):
        for pc in self.pcs:
            if pc.get("qr") and pc["qr"] == qr:
                return pc
        return self.buscar_por_id(qr.strip().upper())  # compatibilidad: QR que ya era "PC-01"

    def siguiente_id(self):
        nums = [int(m.group(1)) for pc in self.pcs
                if (m := re.fullmatch(r"PC-(\d+)", pc["id"]))]
        return f"PC-{(max(nums) if nums else 0) + 1:02d}"

    def guardar_todo(self):
        guardar_json(ARCHIVO_JSON, self.pcs)
        self.lbl_guardado.config(text=f"💾 Guardado automático ✔ {datetime.now():%H:%M:%S}")

    def procesar_qr_automatico(self, qr_data):
        """Se ejecuta en el hilo principal cuando se detecta un QR."""
        self.dialogo_abierto = True
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
                # QR desconocido → pedir ID manual (sugerido: siguiente PC-XX)
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
                        messagebox.showerror("Error", f"{pc_id} ya tiene otro QR vinculado.")
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
                                       f"La {pc['id']} está disponible.\n¿Deseas prestarla?"):
                    self.ent_persona.focus_set()
                else:
                    self.deseleccionar()
            else:
                if messagebox.askyesno(
                        "PC en préstamo",
                        f"La {pc['id']} está prestada a '{pc['persona']}'.\n"
                        "¿Deseas DEVOLVERLA y dejarla disponible?"):
                    self.devolver(pc["id"])
        finally:
            self.dialogo_abierto = False
            self.bloqueo_hasta = time.time() + 3

    def agregar_pc_manual(self):
        entrada = simpledialog.askstring("Agregar PC", "ID de la nueva PC:",
                                         initialvalue=self.siguiente_id(), parent=self.root)
        if not entrada or not entrada.strip():
            return
        pc_id = normalizar_id(entrada)
        if self.buscar_por_id(pc_id):
            messagebox.showerror("Error", f"La computadora {pc_id} ya existe.")
            return
        pc = pc_vacia(pc_id)
        self.pcs.append(pc)
        self.guardar_todo()
        self.refrescar_tablas()
        self.cargar_pc(pc)

    def devolver_seleccionada(self):
        if not self.pc_actual:
            messagebox.showwarning("Aviso", "Selecciona o escanea una PC primero.")
            return
        pc = self.buscar_por_id(self.pc_actual)
        if pc and pc["estado"] == "Disponible":
            messagebox.showinfo("Información", f"{pc['id']} ya está disponible.")
            return
        if messagebox.askyesno("Confirmar", f"¿Devolver {self.pc_actual}?"):
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
            messagebox.showwarning("Aviso", "Selecciona o escanea la PC a eliminar.")
            return
        if messagebox.askyesno("Confirmar", f"¿Eliminar permanentemente la {self.pc_actual}?"):
            self.pcs = [pc for pc in self.pcs if pc["id"] != self.pc_actual]
            if self._after_id:
                self.root.after_cancel(self._after_id)
                self._after_id = None
            self.guardar_todo()
            self.deseleccionar()
            self.refrescar_tablas()

    # ------------------------------- Formulario y autoguardado -------------------------------
    def cargar_pc(self, pc):
        """Carga los datos de la PC en el formulario (autorrellenado)."""
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
        else:
            qr = pc.get("qr", "")
            pc.update(pc_vacia(pc["id"], qr))
        self.guardar_todo()
        self.lbl_sel.config(text=f"{pc['id']} · {pc['estado']}")
        self.refrescar_tablas()

    # ------------------------------- Tablas -------------------------------
    def refrescar_tablas(self):
        sel = self.pc_actual
        self._cargando = True
        for t in (self.tree_disp, self.tree_usadas):
            t.delete(*t.get_children())
        libres = 0
        for pc in self.pcs:
            if pc["estado"] == "Disponible":
                libres += 1
                self.tree_disp.insert("", tk.END, iid=pc["id"], values=(pc["id"], "🟢 Libre"),
                                      tags=("libre",))
            else:
                self.tree_usadas.insert("", tk.END, iid=pc["id"],
                                        values=(pc["id"], pc["persona"], pc["docente"],
                                                pc["materia"], pc["dia"], pc["horario"]),
                                        tags=("ocupada",))
        self.lbl_disp.config(text=f"Computadoras disponibles ({libres})")
        self.lbl_usadas.config(text=f"Computadoras en préstamo ({len(self.pcs) - libres})")
        if sel:
            for t in (self.tree_disp, self.tree_usadas):
                if t.exists(sel):
                    t.selection_set(sel)
                    t.see(sel)
        self.root.after(50, lambda: setattr(self, "_cargando", False))

    def on_seleccion_tabla(self, event):
        tree = event.widget
        sel = tree.selection()
        if not sel:
            return
        pc_id = sel[0]
        if pc_id == self.pc_actual:
            return
        pc = self.buscar_por_id(pc_id)
        if pc:
            self.flush_autoguardado()
            self.cargar_pc(pc)

    # ------------------------------- Hilo de video/QR -------------------------------
    def lector_serial_dedicado(self):
        buffer = bytearray()
        frame_count = 0
        while self.hilo_activo:
            try:
                if self.conectado and self.ser and self.ser.in_waiting > 0:
                    buffer.extend(self.ser.read(self.ser.in_waiting))

                start_idx = buffer.find(b"\xff\xd8")
                if start_idx != -1:
                    if start_idx > 0:
                        del buffer[:start_idx]

                    if len(buffer) >= 6:
                        frame_size = int.from_bytes(buffer[2:6], byteorder="little")
                        total_len = 6 + frame_size

                        if len(buffer) >= total_len:
                            jpg_data = buffer[6:total_len]
                            del buffer[:total_len]

                            if 1000 < frame_size < 100000:
                                img_np = np.frombuffer(jpg_data, dtype=np.uint8)
                                img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

                                if img is not None:
                                    frame_count += 1
                                    if frame_count % 30 == 0:
                                        print(f"[DEBUG] Fotogramas: {frame_count} "
                                              f"(último: {frame_size} bytes)")

                                    img = cv2.resize(img, (480, 320))

                                    try:
                                        for qr in decode(img):
                                            qr_data = qr.data.decode("utf-8").strip()

                                            # Dispara el evento si no hay diálogo ni pausa activa
                                            if (not self.dialogo_abierto
                                                    and time.time() > self.bloqueo_hasta):
                                                self.dialogo_abierto = True
                                                self.root.after(
                                                    0, lambda d=qr_data: self.procesar_qr_automatico(d))

                                            pts = np.array([qr.polygon], dtype=int)
                                            n_pts = len(pts[0])
                                            for i in range(n_pts):
                                                pt1 = tuple(pts[0][i])
                                                pt2 = tuple(pts[0][(i + 1) % n_pts])
                                                cv2.line(img, pt1, pt2, (0, 255, 0), 3)

                                            x, y = qr.rect.left, qr.rect.top
                                            cv2.putText(img, "QR detectado", (x, max(y - 10, 15)),
                                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                                    except Exception:
                                        pass

                                    self.frame_actual = img
                else:
                    if len(buffer) > 200000:
                        buffer.clear()

                time.sleep(0.001)
            except Exception as e:
                print(f"[ERROR EN HILO SERIAL]: {e}")
                self.conectado = False
                time.sleep(0.1)

    def actualizar_interfaz(self):
        if self.conectado:
            self.lbl_estado.config(text=f"Estado: Conectado en {PORT}", foreground=self.p["libre"])
        else:
            self.lbl_estado.config(text="Estado: Sin conexión / Reconectando...",
                                   foreground=self.p["ocupada"])

        if self.frame_actual is not None:
            img_rgb = cv2.cvtColor(self.frame_actual, cv2.COLOR_BGR2RGB)
            img_tk = ImageTk.PhotoImage(image=Image.fromarray(img_rgb))
            self.lbl_video.imgtk = img_tk
            self.lbl_video.config(image=img_tk)

        self.root.after(15, self.actualizar_interfaz)

    def on_closing(self):
        self.flush_autoguardado()
        self.hilo_activo = False
        try:
            if self.ser and self.ser.is_open:
                if self.linterna_encendida:
                    self.ser.write(b"0")
                self.ser.close()
        except Exception:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = GestorIntegralApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()