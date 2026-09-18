import cv2
import json
import serial
import time
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
from datetime import datetime

print("[SISTEMA] Iniciando Caja Registradora (Modo Cámara Web PC)...")

# ==========================
# CONFIGURACION DE PUERTOS
# ==========================
PUERTO_ARDUINO = "COM4"
BAUDIOS_ARDUINO = 9600

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


# ==========================
# HARDWARE Y BASE DE DATOS
# ==========================
detector_qr = cv2.QRCodeDetector()

# Inicializar la cámara de la PC (0 suele ser la cámara web principal)
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("[ERROR] No se pudo acceder a la cámara de la PC.")

carrito_datos = {}

try:
    arduino = serial.Serial()
    arduino.port = PUERTO_ARDUINO
    arduino.baudrate = BAUDIOS_ARDUINO
    arduino.timeout = 1
    arduino.setDTR(False)
    arduino.setRTS(False)
    arduino.open()
    print("[OK] Conexión exitosa con Arduino")
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
    print(f"[BASE DE DATOS] Catálogo cargado ({len(productos)} productos).")
except Exception:
    productos = {}


def cerrar_programa():
    try:
        enviar_arduino(CMD_SALIR)
    except Exception:
        pass

    if cap.isOpened():
        cap.release()

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
ventana.title("🛒 Punto de Venta QR - Cámara PC")
ventana.geometry("1100x750")
ventana.configure(bg="#121212")

style = ttk.Style()
style.theme_use("default")
style.configure("Treeview", background="#1e1e1e", foreground="white", rowheight=30, fieldbackground="#1e1e1e", font=("Arial", 11))
style.map('Treeview', background=[('selected', '#28a745')])
style.configure("Treeview.Heading", background="#333333", foreground="white", font=("Arial", 12, "bold"))

titulo = tk.Label(ventana, text="💳 PUNTO DE VENTA QR (CÁMARA PC)", font=("Segoe UI", 24, "bold"), bg="#121212", fg="#00d2ff")
titulo.pack(pady=15)

main_frame = tk.Frame(ventana, bg="#121212")
main_frame.pack(fill="both", expand=True, padx=20, pady=10)

left_frame = tk.Frame(main_frame, bg="#121212")
left_frame.pack(side="left", fill="both")

label_video = tk.Label(left_frame, bg="black", width=500, height=380, bd=2, relief="groove")
label_video.pack(pady=5)

label_estado_cam = tk.Label(left_frame, text="📡 Cámara PC: Activa", font=("Arial", 10, "bold"), bg="#121212", fg="#28a745")
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
        messagebox.showwarning("Aviso", "El carrito está vacío.")
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
    messagebox.showinfo("Ticket Generado", f"Se guardó el {nombre_archivo} correctamente.")


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
# BUCLE PRINCIPAL
# ==========================
def actualizar():
    global ultimo_codigo, ultimo_tiempo, contador_cuadros

    ret, frame = cap.read()

    if not ret or frame is None:
        label_estado_cam.config(text="📡 Cámara PC: Sin señal", fg="#dc3545")
        ventana.after(10, actualizar)
        return

    contador_cuadros += 1

    # Escanear QR cada 3 cuadros para mantener fluidez
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

    # Renderizado del fotograma
    frame_resized = cv2.resize(frame, (500, 380), interpolation=cv2.INTER_NEAREST)
    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame_rgb)
    imgtk = ImageTk.PhotoImage(image=img)
    label_video.imgtk = imgtk
    label_video.configure(image=imgtk)

    ventana.after(10, actualizar)


actualizar()
ventana.protocol("WM_DELETE_WINDOW", cerrar_programa)
print("[SISTEMA] Interfaz iniciada con la cámara de la PC.")
ventana.mainloop()