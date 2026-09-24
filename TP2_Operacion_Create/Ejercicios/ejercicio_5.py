<<<<<<< HEAD
# Creamos una función encargada de registrar un nuevo alumno
def registrar_nuevo_alumno():

    # Pedimos los datos de texto
    nombre = input("Ingrese el nombre: ")
    apellido = input("Ingrese el apellido: ")

    # Intentamos convertir los datos numéricos
    try:
        # Convertimos el DNI a entero
        dni = int(input("Ingrese el DNI: "))

        # Convertimos la edad a entero
        edad = int(input("Ingrese la edad: "))

    # Si el usuario ingresa texto en lugar de números,
    # se ejecuta este bloque
    except ValueError:
        print("Error: el DNI y la edad deben ser números.")
        return

    # Creamos el diccionario con los datos del alumno
    alumno = {
        "nombre": nombre,
        "apellido": apellido,
        "dni": dni,
        "edad": edad
    }

    # Abrimos el archivo en modo agregar.
    # Si no existe, Python lo crea.
    with open("alumnos.txt", "a", encoding="utf-8") as archivo:

        # Escribimos el diccionario en una nueva línea
        archivo.write(str(alumno) + "\n")

    # Informamos que el registro fue guardado
    print("Alumno guardado correctamente.")


# Llamamos a la función para ejecutar el registro
=======
# Creamos una función encargada de registrar un nuevo alumno
def registrar_nuevo_alumno():

    # Pedimos los datos de texto
    nombre = input("Ingrese el nombre: ")
    apellido = input("Ingrese el apellido: ")

    # Intentamos convertir los datos numéricos
    try:
        # Convertimos el DNI a entero
        dni = int(input("Ingrese el DNI: "))

        # Convertimos la edad a entero
        edad = int(input("Ingrese la edad: "))

    # Si el usuario ingresa texto en lugar de números,
    # se ejecuta este bloque
    except ValueError:
        print("Error: el DNI y la edad deben ser números.")
        return

    # Creamos el diccionario con los datos del alumno
    alumno = {
        "nombre": nombre,
        "apellido": apellido,
        "dni": dni,
        "edad": edad
    }

    # Abrimos el archivo en modo agregar.
    # Si no existe, Python lo crea.
    with open("alumnos.txt", "a", encoding="utf-8") as archivo:

        # Escribimos el diccionario en una nueva línea
        archivo.write(str(alumno) + "\n")

    # Informamos que el registro fue guardado
    print("Alumno guardado correctamente.")


# Llamamos a la función para ejecutar el registro
>>>>>>> 77ab13a377bbad5c616cd57d66bf8bde3bb556b5
registrar_nuevo_alumno()