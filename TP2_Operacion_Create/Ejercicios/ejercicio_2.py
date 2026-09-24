
# Creamos una lista vacía donde se guardarán todos los alumnos
alumnos = []

# Preguntamos cuántos alumnos se desean registrar
cantidad = int(input("¿Cuántos alumnos desea registrar? "))

# Repetimos el proceso la cantidad de veces indicada
for i in range(cantidad):

    # Creamos un diccionario vacío para el alumno actual
    alumno = {}

    # Mostramos qué alumno estamos registrando
    print("\nAlumno", i + 1)

    # Pedimos los datos del alumno
    nombre = input("Ingrese el nombre: ")
    apellido = input("Ingrese el apellido: ")
    dni = int(input("Ingrese el DNI: "))
    promedio = float(input("Ingrese el promedio: "))

    # Guardamos los datos en el diccionario
    alumno["nombre"] = nombre
    alumno["apellido"] = apellido
    alumno["dni"] = dni
    alumno["promedio"] = promedio

    # Agregamos el diccionario a la lista general
    alumnos.append(alumno)

# Mostramos todos los alumnos registrados
print("\nLista completa de alumnos:")

# Creamos una lista vacía donde se guardarán todos los alumnos
alumnos = []

# Preguntamos cuántos alumnos se desean registrar
cantidad = int(input("¿Cuántos alumnos desea registrar? "))

# Repetimos el proceso la cantidad de veces indicada
for i in range(cantidad):

    # Creamos un diccionario vacío para el alumno actual
    alumno = {}

    # Mostramos qué alumno estamos registrando
    print("\nAlumno", i + 1)

    # Pedimos los datos del alumno
    nombre = input("Ingrese el nombre: ")
    apellido = input("Ingrese el apellido: ")
    dni = int(input("Ingrese el DNI: "))
    promedio = float(input("Ingrese el promedio: "))

    # Guardamos los datos en el diccionario
    alumno["nombre"] = nombre
    alumno["apellido"] = apellido
    alumno["dni"] = dni
    alumno["promedio"] = promedio

    # Agregamos el diccionario a la lista general
    alumnos.append(alumno)

# Mostramos todos los alumnos registrados
print("\nLista completa de alumnos:")

print(alumnos)
