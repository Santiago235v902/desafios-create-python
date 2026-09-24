<<<<<<< HEAD
# Creamos una lista vacía para almacenar los alumnos
alumnos = []

# Iniciamos un bucle que continuará indefinidamente
while True:

    # Pedimos el DNI al usuario
    entrada = input("Ingrese el DNI o escriba SALIR para terminar: ")

    # Verificamos si el usuario quiere terminar
    if entrada.upper() == "SALIR":
        break

    # Convertimos el DNI ingresado a número entero
    dni = int(entrada)

    # Variable que indica si el DNI ya existe
    dni_repetido = False

    # Recorremos la lista para buscar el DNI
    for alumno in alumnos:

        # Comparamos el DNI ingresado con el DNI de cada alumno
        if alumno["dni"] == dni:
            dni_repetido = True
            break

    # Si el DNI ya existe, rechazamos el registro
    if dni_repetido:
        print("Error: ese DNI ya está registrado.")
        continue

    # Si el DNI no existe, pedimos el resto de los datos
    nombre = input("Ingrese el nombre: ")
    apellido = input("Ingrese el apellido: ")
    edad = int(input("Ingrese la edad: "))
    promedio = float(input("Ingrese el promedio: "))

    # Creamos el diccionario del nuevo alumno
    alumno = {
        "nombre": nombre,
        "apellido": apellido,
        "dni": dni,
        "edad": edad,
        "promedio": promedio
    }

    # Guardamos el nuevo alumno en la lista
    alumnos.append(alumno)

    # Informamos que el registro fue creado correctamente
    print("Alumno registrado correctamente.")

# Mostramos todos los alumnos al finalizar
print("\nLista final de alumnos:")
=======
# Creamos una lista vacía para almacenar los alumnos
alumnos = []

# Iniciamos un bucle que continuará indefinidamente
while True:

    # Pedimos el DNI al usuario
    entrada = input("Ingrese el DNI o escriba SALIR para terminar: ")

    # Verificamos si el usuario quiere terminar
    if entrada.upper() == "SALIR":
        break

    # Convertimos el DNI ingresado a número entero
    dni = int(entrada)

    # Variable que indica si el DNI ya existe
    dni_repetido = False

    # Recorremos la lista para buscar el DNI
    for alumno in alumnos:

        # Comparamos el DNI ingresado con el DNI de cada alumno
        if alumno["dni"] == dni:
            dni_repetido = True
            break

    # Si el DNI ya existe, rechazamos el registro
    if dni_repetido:
        print("Error: ese DNI ya está registrado.")
        continue

    # Si el DNI no existe, pedimos el resto de los datos
    nombre = input("Ingrese el nombre: ")
    apellido = input("Ingrese el apellido: ")
    edad = int(input("Ingrese la edad: "))
    promedio = float(input("Ingrese el promedio: "))

    # Creamos el diccionario del nuevo alumno
    alumno = {
        "nombre": nombre,
        "apellido": apellido,
        "dni": dni,
        "edad": edad,
        "promedio": promedio
    }

    # Guardamos el nuevo alumno en la lista
    alumnos.append(alumno)

    # Informamos que el registro fue creado correctamente
    print("Alumno registrado correctamente.")

# Mostramos todos los alumnos al finalizar
print("\nLista final de alumnos:")
>>>>>>> 77ab13a377bbad5c616cd57d66bf8bde3bb556b5
print(alumnos)