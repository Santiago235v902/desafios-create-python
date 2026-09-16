# Paso 1: Crear una lista vacía llamada sistema_alumnos
sistema_alumnos = []

print("--- Sistema de Matrícula Continua ---")
print("Escribe 'salir' en el nombre para finalizar.\n")

# Paso 2: Iniciar un bucle while True
while True:
    # Paso 3: Pedir el nombre
    nombre = input("Ingresa el nombre del alumno: ")
    
    # Paso 4: Control para salir del bucle
    if nombre.lower() == "salir":
        break
    
    # Pedimos datos adicionales para completar el perfil
    curso = input("Ingresa el curso: ")
    
    # Creamos el diccionario para este alumno específico
    nuevo_alumno = {
        "nombre": nombre,
        "curso": curso
    }
    
    # Añadimos el diccionario a la lista global
    sistema_alumnos.append(nuevo_alumno)
    print(f"-> ¡Alumno '{nombre}' agregado exitosamente!\n")

# Reporte final
print("\n--- Registro Finalizado ---")
print(f"Total de alumnos matriculados: {len(sistema_alumnos)}")
print("Listado completo de registros:")
print(sistema_alumnos)