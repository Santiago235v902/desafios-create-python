import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

print("[SISTEMA] Iniciando Administrador de Computadoras (Modo Solo Interfaz)...")

ARCHIVO_JSON = "computadoras_asignadas.json"

# Estructura de datos: { codigo_qr: {"pc_id": ..., "profesor": ..., "curso": ...} }
computadoras_prestadas = {}

try:
    with open(ARCHIVO_JSON, "r", encoding="utf8") as f:
        computadoras_prestadas = json.load(f)
    print(f"[BASE DE DATOS] Registro cargado ({len(computadoras_prestadas)} PCs prestadas).")
except Exception:
    computadoras_prestadas = {}


def cerrar_programa():
    ventana.destroy()


# ==========================
# INTERFAZ GRAFICA
# ==========================
ventana = tk.Tk()
ventana.title("💻 Administrador de Computadoras - Panel de Control")
ventana.geometry("1000x650")
ventana.configure(bg="#121212")

style = ttk.Style()
style.theme_use("default")
style.configure("Treeview", background="#1e1e1e", foreground="white", rowheight=35, fieldbackground="#1e1e1e", font=("Arial", 11))
style.map('Treeview', background=[('selected', '#28a745')])
style.configure("Treeview.Heading", background="#333333", foreground="white", font=("Arial", 12, "bold"))

titulo = tk.Label(ventana, text="💻 ADMINISTRADOR DE COMPUTADORAS", font=("Segoe UI", 22, "bold"), bg="#121212", fg="#00d2ff")
titulo.pack(pady=20)

main_frame = tk.Frame(ventana, bg="#121212")
main_frame.pack(fill="both", expand=True, padx=25, pady=10)

# Panel Izquierdo: Acciones Rápidas
left_frame = tk.Frame(main_frame, bg="#1e1e1e", bd=2, relief="ridge", padx=20, pady=20)
left_frame.pack(side="left", fill="y", padx=(0, 20))

tk.Label(left_frame, text="⚙️ ACCIONES", font=("Segoe UI", 16, "bold"), bg="#1e1e1e", fg="white").pack(pady=(0, 20))

def registrar_o_actualizar_pc():
    codigo = simpledialog.askstring("Préstamo de PC", "Ingrese el Código o ID único de la PC (o QR):", parent=ventana)
    if not codigo:
        return
    codigo = codigo.strip()

    profesor = simpledialog.askstring("Préstamo de PC", f"PC [{codigo}]\n\nIngrese el nombre del Profesor/a:", parent=ventana)
    if not profesor:
        return

    curso = simpledialog.askstring("Préstamo de PC", "Ingrese el Curso (ej. 4to A, 5to B):", parent=ventana)
    if not curso:
        return

    pc_id = simpledialog.askstring("Préstamo de PC", "Ingrese el identificador visible de la PC (ej. PC-05):", parent=ventana)
    if not pc_id:
        pc_id = f"PC-{codigo}"

    # Sobrescribe automáticamente si el código ya existe
    computadoras_prestadas[codigo] = {
        "pc_id": pc_id,
        "profesor": profesor,
        "curso": curso
    }

    refrescar_interfaz_pcs()
    messagebox.showinfo("Éxito", f"Computadora {pc_id} asignada correctamente a {profesor} ({curso}).")

tk.Button(left_frame, text="➕ Asignar / Sobrescribir PC", bg="#28a745", fg="white", font=("Arial", 11, "bold"),
          command=registrar_o_actualizar_pc, width=22, relief="flat", pady=8).pack(pady=10)

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
        messagebox.showinfo("Éxito", f"La PC {pc_id} ha sido liberada.")

tk.Button(left_frame, text="↩️ Liberar / Devolver PC", bg="#dc3545", fg="white", font=("Arial", 11, "bold"),
          command=liberar_computadora, width=22, relief="flat", pady=8).pack(pady=10)

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
        "CÓDIGO | ID PC | PROFESOR | CURSO\n"
        "-------------------------------------\n"
    )
    for cod, data in computadoras_prestadas.items():
        contenido += f"{cod} | {data['pc_id']} | {data['profesor']} | {data['curso']}\n"
    contenido += "=====================================\n"
    
    with open(nombre_archivo, "w", encoding="utf8") as f:
        f.write(contenido)

    messagebox.showinfo("Reporte Generado", f"Se guardó el archivo {nombre_archivo} correctamente.")

tk.Button(left_frame, text="📄 Exportar Reporte", bg="#007bff", fg="white", font=("Arial", 11, "bold"),
          command=exportar_reporte, width=22, relief="flat", pady=8).pack(pady=10)


# Panel Derecho: Tabla de Registros
right_frame = tk.Frame(main_frame, bg="#1e1e1e", bd=2, relief="ridge")
right_frame.pack(side="right", fill="both", expand=True)

tk.Label(right_frame, text="📋 COMPUTADORAS PRESTADAS ACTUALMENTE", font=("Segoe UI", 16, "bold"), bg="#1e1e1e", fg="white").pack(pady=15)

columnas = ("codigo", "pc_id", "profesor", "curso")
tabla_pcs = ttk.Treeview(right_frame, columns=columnas, show="headings", height=14)
tabla_pcs.heading("codigo", text="Código / QR")
tabla_pcs.heading("pc_id", text="ID / Nº PC")
tabla_pcs.heading("profesor", text="Profesor")
tabla_pcs.heading("curso", text="Curso")
tabla_pcs.column("codigo", width=120, anchor="w")
tabla_pcs.column("pc_id", width=90, anchor="center")
tabla_pcs.column("profesor", width=160, anchor="w")
tabla_pcs.column("curso", width=120, anchor="w")
tabla_pcs.pack(fill="both", expand=True, padx=20, pady=10)

total_prestamos_label = tk.Label(right_frame, text="TOTAL PRESTADAS: 0", font=("Segoe UI", 16, "bold"), bg="#1e1e1e", fg="#ffcc00")
total_prestamos_label.pack(pady=15)


def refrescar_interfaz_pcs():
    for fila in tabla_pcs.get_children():
        tabla_pcs.delete(fila)
    
    for codigo, data in computadoras_prestadas.items():
        tabla_pcs.insert("", "end", iid=codigo, values=(codigo, data["pc_id"], data["profesor"], data["curso"]))
    
    total_prestamos_label.config(text=f"TOTAL PRESTADAS: {len(computadoras_prestadas)}")
    
    # Guardado automático en JSON
    try:
        with open(ARCHIVO_JSON, "w", encoding="utf8") as f:
            json.dump(computadoras_prestadas, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[ERROR] Al guardar JSON: {e}")


# Cargar datos iniciales
refrescar_interfaz_pcs()
ventana.protocol("WM_DELETE_WINDOW", cerrar_programa)
print("[SISTEMA] Interfaz iniciada correctamente.")
ventana.mainloop()