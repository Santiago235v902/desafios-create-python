import cv2
import json
import serial
import threading
import time
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
from datetime import datetime

print("[SISTEMA] Iniciando Administrador de Computadoras (Modo Alta Velocidad / FPS Max)...")

# ==========================
# CONFIGURACION DE PUERTOS
# ==========================
PUERTO_ARDUINO = "COM4"
BAUDIOS_ARDUINO = 9600

PUERTO_ESP32CAM = "COM7"
BAUDIOS_ESP32CAM = 460800  # 4x más rápido que 115200

ARCHIVO_JSON = "computadoras_asignadas.json"

# Comandos hacia Arduino (Se conservan por compatibilidad de hardware)
CMD_INICIO           = 'B'
CMD_BEEP_ESCANEO     = 'D'
CMD_MOSTRAR_PRODUCTO = 'P'
CMD_COMBO_SECRETO    = 'Z'
CMD_COMBO_10         = 'K'
CMD_ABRIR_PUERTA     = 'O'
CMD_CERRAR_PUERTA    = 'C'
CMD_TICKET           = 'S'
CMD_TOTAL            = 'T'
CMD_ELIMINAR         = 'E'
CMD_CARRITO_VACIO    = 'X'
CMD_SALIR            = 'Q'

MARCADOR = b'\xAA\xBB\xCC\xDD'


# ==========================
# RECEPTOR STREAM ESP32-CAM HIGH FPS
# ==========================
class ESP32CamStream:
    def __init__(self, puerto, baudios=460800, timeout=1):
        self.puerto = puerto
        self.baudios = baudios
        self.timeout = timeout
        self.ser = None
        self.frame_actual = None
        self.lock = threading.Lock()
        self.corriendo = False
        self.hilo = None
        self.conectado = False
        self.ultimo_error = None

    def conectar(self):
        try:
            self.ser = serial.Serial(self.puerto, self.baudios, timeout=self.timeout)
            self.ser.setDTR(False)
            self.ser.setRTS(False)
            time.sleep(1.0)
            self.ser.reset_input_buffer()
            self.conectado = True
            self.ultimo_error = None
            print(f"[ESP32-CAM] Conectado a Alta Velocidad en {self.puerto} @ {self.baudios} baudios")
            return True
        except Exception as e:
            self.ultimo_error = str(e)
            self.conectado = False
            print(f"[ESP32-CAM] Error al conectar: {e}")
            return False

    def iniciar(self):
        if not self.conectado:
            if not self.conectar():
                return False
        self.corriendo = True
        self.hilo = threading.Thread(target=self._bucle_lectura, daemon=True)
        self.hilo.start()
        return True

    def _leer_exacto(self, n):
        buf = bytearray()
        while len(buf) < n:
            if not self.corriendo:
                return None
            chunk = self.ser.read(n - len(buf))
            if not chunk:
                return None
            buf.extend(chunk)
        return bytes(buf)

    def _resincronizar(self):
        contador = 0
        tiempo_inicio = time.time()
        while self.corriendo:
            if time.time() - tiempo_inicio > 1.0:
                if self.ser and self.ser.is_open:
                    self.ser.reset_input_buffer()
                return False

            if self.ser and self.ser.in_waiting > 0:
                b = self.ser.read(1)
                if not b:
                    return False
                if b[0] == MARCADOR[contador]:
                    contador += 1
                    if contador == len(MARCADOR):
                        return True
                else:
                    contador = 1 if b[0] == MARCADOR[0] else 0
            else:
                time.sleep(0.001)
        return False

    def _bucle_lectura(self):
        errores_seguidos = 0
        while self.corriendo:
            try:
                if not self._resincronizar():
                    continue

                cabecera_longitud = self._leer_exacto(4)
                if cabecera_longitud is None:
                    continue

                longitud = int.from_bytes(cabecera_longitud, byteorder='little')

                if longitud == 0 or longitud > 300_000:
                    if self.ser and self.ser.is_open:
                        self.ser.reset_input_buffer()
                    continue

                datos_jpeg = self._leer_exacto(longitud)
                if datos_jpeg is None:
                    continue

                frame = cv2.imdecode(np.frombuffer(datos_jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    with self.lock:
                        self.frame_actual = frame
                    errores_seguidos = 0
                else:
                    errores_seguidos += 1

            except serial.SerialException as e:
                self.conectado = False
                self.ultimo_error = str(e)
                time.sleep(1)
                self._reintentar_conexion()
            except Exception:
                errores_seguidos += 1

            if errores_seguidos > 10:
                if self.ser and self.ser.is_open:
                    self.ser.reset_input_buffer()
                errores_seguidos = 0

    def _reintentar_conexion(self):
        try:
            if self.ser:
                self.ser.close()
        except Exception:
            pass
        while self.corriendo and not self.conectado:
            if self.conectar():
                break
            time.sleep(1.5)

    def obtener_frame(self):
        with self.lock:
            if self.frame_actual is not None:
                return self.frame_actual.copy()
        return None

    def detener(self):
        self.corriendo = False
        if self.hilo:
            self.hilo.join(timeout=2)
        if self.ser and self.ser.is_open:
            self.ser.close()
        print("[ESP32-CAM] Detenido.")


# ==========================
# HARDWARE Y BASE DE DATOS
# ==========================
detector_qr = cv2.QRCodeDetector()

esp32cam = ESP32CamStream(PUERTO_ESP32CAM, BAUDIOS_ESP32CAM)
if not esp32cam.iniciar():
    print(f"[ERROR] No se pudo iniciar el stream en {PUERTO_ESP32CAM}")

# Almacena las computadoras activas actualmente prestadas
# Estructura: { codigo_qr_pc: {"pc_id": ..., "profesor": ..., "curso": ...} }
computadoras_prestadas = {}

try:
    arduino = serial.Serial()
    arduino.port = PUERTO_ARDUINO
    arduino.baudrate = BAUDIOS_ARDUINO
    arduino.timeout = 1
    arduino.setDTR(False)
    arduino.setRTS(False)
    arduino.open()
    print("[OK] Conexion exitosa con Arduino")
    time.sleep(1.5)
except Exception as e:
    print(f"[ERROR] Arduino no detectado en {PUERTO_ARDUINO}: {e}")
    arduino = None


def enviar_arduino(comando):
    if arduino and arduino.is_open:
        try:
            arduino.write(comando.encode('utf-8'))
            arduino.flush()
        except Exception as e:
            print(f"[ERROR ARDUINO]: {e}")


enviar_arduino(CMD_INICIO)

try:
    with open(ARCHIVO_JSON, "r", encoding="utf8") as f:
        computadoras_prestadas = json.load(f)
    print(f"[BASE DE DATOS] Registro cargado ({len(computadoras_prestadas)} PCs prestadas).")
except Exception:
    computadoras_prestadas = {}


def cerrar_programa():
    try:
        enviar_arduino(CMD_SALIR)
    except Exception:
        pass

    esp32cam.detener()

    if arduino and arduino.is_open:
        arduino.close()

    ventana.destroy()


ultimo_codigo = ""
ultimo_tiempo = 0
contador_cuadros = 0  # Para intercalar escaneo de QR y mantener FPS altos

# ==========================
# INTERFAZ GRAFICA
# ==========================
ventana = tk.Tk()
ventana.title("💻 Administrador de Computadoras - Alta Velocidad")
ventana.geometry("1100x750")
ventana.configure(bg="#121212")

style = ttk.Style()
style.theme_use("default")
style.configure("Treeview", background="#1e1e1e", foreground="white", rowheight=30, fieldbackground="#1e1e1e", font=("Arial", 11))
style.map('Treeview', background=[('selected', '#28a745')])
style.configure("Treeview.Heading", background="#333333", foreground="white", font=("Arial", 12, "bold"))

titulo = tk.Label(ventana, text="💻 ADMINISTRADOR DE COMPUTADORAS (QR)", font=("Segoe UI", 22, "bold"), bg="#121212", fg="#00d2ff")
titulo.pack(pady=15)

main_frame = tk.Frame(ventana, bg="#121212")
main_frame.pack(fill="both", expand=True, padx=20, pady=10)

left_frame = tk.Frame(main_frame, bg="#121212")
left_frame.pack(side="left", fill="both")

label_video = tk.Label(left_frame, bg="black", width=500, height=380, bd=2, relief="groove")
label_video.pack(pady=5)

label_estado_cam = tk.Label(left_frame, text="📡 Camara: conectando...", font=("Arial", 10, "bold"), bg="#121212", fg="#ffcc00")
label_estado_cam.pack(pady=(0, 5))

label_info = tk.Label(left_frame, text="✅ Sistema Listo. Escanee el QR de una computadora.", font=("Arial", 13, "bold"), bg="#121212", fg="#28a745")
label_info.pack(pady=10)

frame_servo_manual = tk.Frame(left_frame, bg="#121212")
frame_servo_manual.pack(pady=5)

tk.Button(frame_servo_manual, text="🔓 Abrir Puerta", bg="#17a2b8", fg="white", font=("Arial", 10, "bold"),
          command=lambda: enviar_arduino(CMD_ABRIR_PUERTA), width=15, relief="flat").pack(side="left", padx=5)
tk.Button(frame_servo_manual, text="🔒 Cerrar Puerta", bg="#6c757d", fg="white", font=("Arial", 10, "bold"),
          command=lambda: enviar_arduino(CMD_CERRAR_PUERTA), width=15, relief="flat").pack(side="left", padx=5)

right_frame = tk.Frame(main_frame, bg="#1e1e1e", bd=2, relief="ridge")
right_frame.pack(side="right", fill="both", expand=True, padx=(20, 0))

tk.Label(right_frame, text="📋 COMPUTADORAS PRESTADAS", font=("Segoe UI", 16, "bold"), bg="#1e1e1e", fg="white").pack(pady=10)

columnas = ("codigo", "pc_id", "profesor", "curso")
tabla_pcs = ttk.Treeview(right_frame, columns=columnas, show="headings", height=12)
tabla_pcs.heading("codigo", text="Código QR")
tabla_pcs.heading("pc_id", text="ID / Nº PC")
tabla_pcs.heading("profesor", text="Profesor")
tabla_pcs.heading("curso", text="Curso")
tabla_pcs.column("codigo", width=110, anchor="w")
tabla_pcs.column("pc_id", width=80, anchor="center")
tabla_pcs.column("profesor", width=140, anchor="w")
tabla_pcs.column("curso", width=110, anchor="w")
tabla_pcs.pack(fill="x", padx=15, pady=5)

total_prestamos_label = tk.Label(right_frame, text="TOTAL PRESTADAS: 0", font=("Segoe UI", 18, "bold"), bg="#1e1e1e", fg="#ffcc00")
total_prestamos_label.pack(pady=15)


def refrescar_interfaz_pcs():
    for fila in tabla_pcs.get_children():
        tabla_pcs.delete(fila)
    
    for codigo, data in computadoras_prestadas.items():
        tabla_pcs.insert("", "end", iid=codigo, values=(codigo, data["pc_id"], data["profesor"], data["curso"]))
    
    total_prestamos_label.config(text=f"TOTAL PRESTADAS: {len(computadoras_prestadas)}")
    
    # Guardar cambios automáticamente en JSON
    try:
        with open(ARCHIVO_JSON, "w", encoding="utf8") as f:
            json.dump(computadoras_prestadas, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[ERROR] Al guardar JSON: {e}")


def exportar_reporte():
    if not computadoras_prestadas:
        messagebox.showwarning("Aviso", "No hay computadoras registradas actualmente.")
        return
    
    fecha = datetime.now()
    nombre_archivo = f"reporte_pcs_{fecha.strftime('%Y%m%d_%H%M%S')}.txt"
    contenido = (
        "====== REPORTE DE COMPUTADORAS ======\n"
        f"Fecha: {fecha.strftime('%Y-%m-%d %H:%M:%S')}\n"
        "-------------------------------------\n"
        "CÓDIGO QR | ID PC | PROFESOR | CURSO\n"
        "-------------------------------------\n"
    )
    for cod, data in computadoras_prestadas.items():
        contenido += f"{cod} | {data['pc_id']} | {data['profesor']} | {data['curso']}\n"
    contenido += "=====================================\n"
    
    with open(nombre_archivo, "w", encoding="utf8") as f:
        f.write(contenido)

    messagebox.showinfo("Reporte Generado", f"Se guardó el archivo {nombre_archivo} correctamente.")


def liberar_computadora():
    seleccion = tabla_pcs.selection()
    if not seleccion:
        messagebox.showwarning("Aviso", "Selecciona una computadora de la lista para liberar.")
        return
    codigo_seleccionado = seleccion[0]
    pc_id = computadoras_prestadas[codigo_seleccionado]["pc_id"]
    
    if messagebox.askyesno("Confirmar", f"¿Marcar la PC '{pc_id}' como devuelta / libre?"):
        del computadoras_prestadas[codigo_seleccionado]
        refrescar_interfaz_pcs()
        enviar_arduino(CMD_ELIMINAR)
        messagebox.showinfo("Éxito", f"La PC {pc_id} ha sido liberada.")


frame_botones = tk.Frame(right_frame, bg="#1e1e1e")
frame_botones.pack(pady=10)
tk.Button(frame_botones, text="↩️ Liberar / Devolver PC", bg="#dc3545", fg="white", font=("Arial", 11, "bold"),
          command=liberar_computadora, width=18, relief="flat").pack(side="left", padx=5)
tk.Button(frame_botones, text="📄 Exportar Reporte", bg="#007bff", fg="white", font=("Arial", 11, "bold"),
          command=exportar_reporte, width=18, relief="flat").pack(side="left", padx=5)


# ==========================
# BUCLE PRINCIPAL ULTRA FLUIDO
# ==========================
def actualizar():
    global ultimo_codigo, ultimo_tiempo, contador_cuadros

    frame = esp32cam.obtener_frame()

    if esp32cam.conectado and frame is not None:
        label_estado_cam.config(text="📡 Camara: Fluida (460.8K Baudios)", fg="#28a745")
    else:
        label_estado_cam.config(text="📡 Camara: Reintentando...", fg="#dc3545")

    if frame is not None:
        contador_cuadros += 1

        # Escanear QR solo cada 3 cuadros para NO reducir los FPS del video
        if contador_cuadros % 3 == 0:
            codigo, _, _ = detector_qr.detectAndDecode(frame)

            if codigo:
                codigo = codigo.strip()
                ahora = time.time()

                if codigo != ultimo_codigo or (ahora - ultimo_tiempo > 2.5):
                    ultimo_codigo = codigo
                    ultimo_tiempo = ahora

                    # Preguntar datos del profesor y curso (permite registrar o sobreescribir)
                    profesor_ingresado = simpledialog.askstring("Préstamo de PC", f"Escaneado QR: {codigo}\n\nIngrese el nombre del Profesor/a:", parent=ventana)
                    
                    if profesor_ingresado:
                        curso_ingresado = simpledialog.askstring("Préstamo de PC", "Ingrese el Curso (ej. 4to A, 5to B):", parent=ventana)
                        if curso_ingresado:
                            pc_id_ingresado = simpledialog.askstring("Préstamo de PC", "Ingrese el ID o Número de la Computadora (ej. PC-05):", parent=ventana)
                            if not pc_id_ingresado:
                                pc_id_ingresado = f"PC-{codigo[:5]}"

                            # Se sobreescriben automáticamente si el código QR ya existía
                            computadoras_prestadas[codigo] = {
                                "pc_id": pc_id_ingresado,
                                "profesor": profesor_ingresado,
                                "curso": curso_ingresado
                            }

                            refrescar_interfaz_pcs()

                            enviar_arduino(CMD_MOSTRAR_PRODUCTO)
                            enviar_arduino(f"{pc_id_ingresado}|{profesor_ingresado}\n")

                            label_info.config(text=f"✅ PC {pc_id_ingresado} asignada a {profesor_ingresado}", fg="#28a745")
                        else:
                            label_info.config(text="⚠️ Operación cancelada (falta curso)", fg="orange")
                    else:
                        label_info.config(text="⚠️ Operación cancelada (falta profesor)", fg="orange")

                    ultimo_codigo = codigo
                    ultimo_tiempo = time.time()

        # Renderizado de fotograma ultra rápido
        frame_resized = cv2.resize(frame, (500, 380), interpolation=cv2.INTER_NEAREST)
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        label_video.imgtk = imgtk
        label_video.configure(image=imgtk)

    # 1ms de retardo para maximizar refresco de la pantalla (hasta ~30 FPS)
    ventana.after(1, actualizar)


# Cargar datos iniciales en la interfaz
refrescar_interfaz_pcs()
actualizar()
ventana.protocol("WM_DELETE_WINDOW", cerrar_programa)
print("[SISTEMA] Interfaz de administración de PCs iniciada a alta velocidad.")
ventana.mainloop()