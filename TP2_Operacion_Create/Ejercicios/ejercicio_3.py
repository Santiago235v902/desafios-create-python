<<<<<<< HEAD
# Creamos una lista para almacenar los alumnos válidos
alumnos = []

# Pedimos los datos básicos del alumno
nombre = input("Ingrese el nombre: ")
apellido = input("Ingrese el apellido: ")
dni = int(input("Ingrese el DNI: "))
promedio = float(input("Ingrese el promedio: "))
edad = int(input("Ingrese la edad: "))

# Verificamos si la edad está dentro del rango permitido
if edad >= 17 and edad <= 99:

    # Creamos el diccionario porque la edad es válida
    alumno = {}

    # Guardamos los datos del alumno
    alumno["nombre"] = nombre
    alumno["apellido"] = apellido
    alumno["dni"] = dni
    alumno["promedio"] = promedio
    alumno["edad"] = edad

    # Agregamos el alumno a la lista
    alumnos.append(alumno)

    # Informamos que el registro fue creado correctamente
    print("Alumno registrado correctamente.")

else:

    # Si la edad no es válida, descartamos el registro
    print("Error: la edad debe estar entre 17 y 99 años.")

# Mostramos la lista final
print("Alumnos registrados:")
=======
# Creamos una lista para almacenar los alumnos válidos
alumnos = []

# Pedimos los datos básicos del alumno
nombre = input("Ingrese el nombre: ")
apellido = input("Ingrese el apellido: ")
dni = int(input("Ingrese el DNI: "))
promedio = float(input("Ingrese el promedio: "))
edad = int(input("Ingrese la edad: "))

# Verificamos si la edad está dentro del rango permitido
if edad >= 17 and edad <= 99:

    # Creamos el diccionario porque la edad es válida
    alumno = {}

    # Guardamos los datos del alumno
    alumno["nombre"] = nombre
    alumno["apellido"] = apellido
    alumno["dni"] = dni
    alumno["promedio"] = promedio
    alumno["edad"] = edad

    # Agregamos el alumno a la lista
    alumnos.append(alumno)

    # Informamos que el registro fue creado correctamente
    print("Alumno registrado correctamente.")

else:

    # Si la edad no es válida, descartamos el registro
    print("Error: la edad debe estar entre 17 y 99 años.")

# Mostramos la lista final
print("Alumnos registrados:")
>>>>>>> 77ab13a377bbad5c616cd57d66bf8bde3bb556b5
print(alumnos)