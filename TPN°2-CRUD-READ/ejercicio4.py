libros=[
    {"isbn":1001,"titulo":"Python desde cero","autor":"Juan Pérez","disponible":True},
    {"isbn":1002,"titulo":"Programación web","autor":"Ana López","disponible":False},
    {"isbn":1003,"titulo":"Bases de datos","autor":"Carlos Gómez","disponible":True},
    {"isbn":1004,"titulo":"Algoritmos","autor":"María Torres","disponible":True},
    {"isbn":1005,"titulo":"Programación orientada a objetos","autor":"Pedro Díaz","disponible":False}
]

# Versión incorrecta
def buscar_incorrecto(isbn):
    for libro in libros:
        if libro["isbn"]==isbn:
            print("Libro encontrado:",libro)
        else:
            print("Libro no encontrado")

# El else pertenece al if de cada vuelta del for.
# Por eso puede mostrar "Libro no encontrado" antes de terminar la búsqueda.
# Aunque el libro exista, los registros anteriores que no coincidan muestran el mensaje.
# Además, la búsqueda continúa después de encontrar el libro.

# Versión corregida
def buscar_libro(isbn):
    encontrado=False

    for libro in libros:
        if libro["isbn"]==isbn:
            print("\nISBN:",libro["isbn"])
            print("Título:",libro["titulo"])
            print("Autor:",libro["autor"])
            print("Disponible:",libro["disponible"])
            encontrado=True
            break

    if encontrado==False:
        print("Libro no encontrado")

isbn=int(input("Ingrese el ISBN: "))
buscar_libro(isbn)