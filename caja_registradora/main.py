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

print("[SISTEMA] Iniciando Caja Registradora (Modo Alta Velocidad / FPS Max)...")

# ==========================
# CONFIGURACION DE PUERTOS
# ==========================
PUERTO_ARDUINO = "COM4"
BAUDIOS_ARDUINO = 9600

PUERTO_ESP32CAM = "COM7"
BAUDIOS_ESP32CAM = 460800  # 4x más rápido que 115200

ARCHIVO_JSON = "productos.json"

# Comandos hacia Arduino
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

carrito_datos = {}

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
        productos = json.load(f)
    print(f"[BASE DE DATOS] Catalogo cargado ({len(productos)} productos).")
except Exception:
    productos = {}


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
ventana.title("🛒 Punto de Venta QR - Alta Velocidad (FPS Max)")
ventana.geometry("1100x750")
ventana.configure(bg="#121212")

style = ttk.Style()
style.theme_use("default")
style.configure("Treeview", background="#1e1e1e", foreground="white", rowheight=30, fieldbackground="#1e1e1e", font=("Arial", 11))
style.map('Treeview', background=[('selected', '#28a745')])
style.configure("Treeview.Heading", background="#333333", foreground="white", font=("Arial", 12, "bold"))

titulo = tk.Label(ventana, text="💳 PUNTO DE VENTA QR (FPS MAX)", font=("Segoe UI", 24, "bold"), bg="#121212", fg="#00d2ff")
titulo.pack(pady=15)

main_frame = tk.Frame(ventana, bg="#121212")
main_frame.pack(fill="both", expand=True, padx=20, pady=10)

left_frame = tk.Frame(main_frame, bg="#121212")
left_frame.pack(side="left", fill="both")

label_video = tk.Label(left_frame, bg="black", width=500, height=380, bd=2, relief="groove")
label_video.pack(pady=5)

label_estado_cam = tk.Label(left_frame, text="📡 Camara: conectando...", font=("Arial", 10, "bold"), bg="#121212", fg="#ffcc00")
label_estado_cam.pack(pady=(0, 5))

label_info = tk.Label(left_frame, text="✅ Sistema Listo. Escanee un producto.", font=("Arial", 13, "bold"), bg="#121212", fg="#28a745")
label_info.pack(pady=10)

frame_servo_manual = tk.Frame(left_frame, bg="#121212")
frame_servo_manual.pack(pady=5)

tk.Button(frame_servo_manual, text="🔓 Abrir Puerta", bg="#17a2b8", fg="white", font=("Arial", 10, "bold"),
          command=lambda: enviar_arduino(CMD_ABRIR_PUERTA), width=15, relief="flat").pack(side="left", padx=5)
tk.Button(frame_servo_manual, text="🔒 Cerrar Puerta", bg="#6c757d", fg="white", font=("Arial", 10, "bold"),
          command=lambda: enviar_arduino(CMD_CERRAR_PUERTA), width=15, relief="flat").pack(side="left", padx=5)

right_frame = tk.Frame(main_frame, bg="#1e1e1e", bd=2, relief="ridge")
right_frame.pack(side="right", fill="both", expand=True, padx=(20, 0))

tk.Label(right_frame, text="🛒 DETALLE DE COMPRA", font=("Segoe UI", 16, "bold"), bg="#1e1e1e", fg="white").pack(pady=10)

columnas = ("producto", "cantidad", "precio", "subtotal")
tabla_carrito = ttk.Treeview(right_frame, columns=columnas, show="headings", height=12)
tabla_carrito.heading("producto", text="Producto")
tabla_carrito.heading("cantidad", text="Cant.")
tabla_carrito.heading("precio", text="P. Unit")
tabla_carrito.heading("subtotal", text="Subtotal")
tabla_carrito.column("producto", width=180, anchor="w")
tabla_carrito.column("cantidad", width=60, anchor="center")
tabla_carrito.column("precio", width=90, anchor="e")
tabla_carrito.column("subtotal", width=90, anchor="e")
tabla_carrito.pack(fill="x", padx=15, pady=5)

precio_total = tk.Label(right_frame, text="TOTAL: $0.00", font=("Segoe UI", 22, "bold"), bg="#1e1e1e", fg="#ffcc00")
precio_total.pack(pady=15)


def refrescar_interfaz_carrito():
    for fila in tabla_carrito.get_children():
        tabla_carrito.delete(fila)
    total = 0
    for cod, data in carrito_datos.items():
        subtotal = data["cantidad"] * data["precio"]
        total += subtotal
        tabla_carrito.insert("", "end", iid=cod, values=(data["nombre"], f"x{data['cantidad']}", f"${data['precio']:.2f}", f"${subtotal:.2f}"))
    precio_total.config(text=f"TOTAL: ${total:.2f}")
    return total


def generar_ticket():
    if not carrito_datos:
        enviar_arduino(CMD_CARRITO_VACIO)
        messagebox.showwarning("Aviso", "El carrito esta vacio.")
        return
    total = refrescar_interfaz_carrito()
    fecha = datetime.now()
    nombre_archivo = f"ticket_{fecha.strftime('%Y%m%d_%H%M%S')}.txt"
    contenido = (
        "====== TICKET DE COMPRA ======\n"
        f"Fecha: {fecha.strftime('%Y-%m-%d %H:%M:%S')}\n"
        "------------------------------\n"
        "CANT | PRODUCTO | SUBTOTAL\n"
        "------------------------------\n"
    )
    for data in carrito_datos.values():
        subt = data["cantidad"] * data["precio"]
        contenido += f"x{data['cantidad']} {data['nombre']} - ${subt:.2f}\n"
    contenido += f"------------------------------\nTOTAL A PAGAR: ${total:.2f}\n==============================\n"
    with open(nombre_archivo, "w", encoding="utf8") as f:
        f.write(contenido)

    enviar_arduino(CMD_TICKET)
    enviar_arduino(f"{CMD_TOTAL}{total:.2f}\n")
    carrito_datos.clear()
    refrescar_interfaz_carrito()
    messagebox.showinfo("Ticket Generado", f"Se guardo el {nombre_archivo} correctamente.")


def borrar_producto():
    seleccion = tabla_carrito.selection()
    if not seleccion:
        messagebox.showwarning("Aviso", "Selecciona un producto para eliminar.")
        return
    codigo_seleccionado = seleccion[0]
    nombre_prod = carrito_datos[codigo_seleccionado]["nombre"]
    if messagebox.askyesno("Confirmar", f"¿Eliminar '{nombre_prod}' del carrito?"):
        del carrito_datos[codigo_seleccionado]
        refrescar_interfaz_carrito()
        enviar_arduino(CMD_ELIMINAR)


frame_botones = tk.Frame(right_frame, bg="#1e1e1e")
frame_botones.pack(pady=10)
tk.Button(frame_botones, text="🗑 Eliminar Seleccionado", bg="#dc3545", fg="white", font=("Arial", 11, "bold"),
          command=borrar_producto, width=18, relief="flat").pack(side="left", padx=5)
tk.Button(frame_botones, text="🧾 IMPRIMIR TICKET", bg="#007bff", fg="white", font=("Arial", 11, "bold"),
          command=generar_ticket, width=18, relief="flat").pack(side="left", padx=5)


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

                    if codigo in productos:
                        p = productos[codigo]
                        if codigo in carrito_datos:
                            carrito_datos[codigo]["cantidad"] += 1
                        else:
                            carrito_datos[codigo] = {"nombre": p["nombre"], "precio": float(p["precio"]), "cantidad": 1}

                        refrescar_interfaz_carrito()
                        total_articulos = sum(d["cantidad"] for d in carrito_datos.values())

                        enviar_arduino(CMD_MOSTRAR_PRODUCTO)
                        enviar_arduino(f"{p['nombre']}|{p['precio']:.2f}\n")

                        if total_articulos == 5:
                            enviar_arduino(CMD_COMBO_SECRETO)
                            label_info.config(text="⚔️ ¡5 PRODUCTOS! ¡SECRET FOUND! ⚔️", fg="cyan")
                        elif total_articulos == 10:
                            enviar_arduino(CMD_COMBO_10)
                            label_info.config(text="🔥 ¡COMBO 10 PRODUCTOS! 🔥", fg="#ffcc00")
                        else:
                            label_info.config(text=f"✅ {p['nombre']} agregado", fg="#28a745")
                    else:
                        label_info.config(text="⚙️ CONFIGURANDO PRODUCTO NUEVO", fg="orange")
                        
                        nombre = simpledialog.askstring("Nuevo Producto", "Nombre del producto:", parent=ventana)
                        if nombre:
                            precio = simpledialog.askfloat("Nuevo Producto", "Precio del producto:", parent=ventana)
                            stock = simpledialog.askinteger("Nuevo Producto", "Cantidad en Stock:", parent=ventana)
                            if precio is not None and stock is not None:
                                productos[codigo] = {"nombre": nombre, "precio": precio, "stock": stock}
                                with open(ARCHIVO_JSON, "w", encoding="utf8") as f:
                                    json.dump(productos, f, indent=4, ensure_ascii=False)
                        
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


actualizar()
ventana.protocol("WM_DELETE_WINDOW", cerrar_programa)
print("[SISTEMA] Interfaz iniciada a alta velocidad.")
ventana.mainloop()