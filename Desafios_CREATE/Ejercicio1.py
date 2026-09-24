# 1. Crear un diccionario vacío
alumno = {}

# 2. Pedir datos al usuario
nombre = input("Ingresa el nombre del alumno: ")
edad = int(input("Ingresa la edad del alumno: "))
curso = input("Ingresa el curso del alumno: ")

# 3. Asignar los valores creando las claves correspondientes
alumno["nombre"] = nombre
alumno["edad"] = edad
alumno["curso"] = curso

# 4. Imprimir el diccionario resultante
print("\nPerfil del alumno registrado:")
print(alumno)