ordenes=[
    {"numero":1001,"cliente":"Juan Pérez","equipo":"Notebook Lenovo","falla":"No enciende","estado":"Pendiente","costo":45000},
    {"numero":1002,"cliente":"María Gómez","equipo":"PC Dell","falla":"No inicia Windows","estado":"En reparación","costo":60000},
    {"numero":1003,"cliente":"Lucas Fernández","equipo":"Notebook HP","falla":"Pantalla rota","estado":"Finalizada","costo":90000},
    {"numero":1004,"cliente":"Sofía Rodríguez","equipo":"PC Asus","falla":"Problemas de RAM","estado":"En reparación","costo":55000},
    {"numero":1005,"cliente":"Mateo López","equipo":"Notebook Acer","falla":"Disco dañado","estado":"Pendiente","costo":70000},
    {"numero":1006,"cliente":"Camila Torres","equipo":"PC Lenovo","falla":"Sobrecalentamiento","estado":"Finalizada","costo":35000},
    {"numero":1007,"cliente":"Nicolás Díaz","equipo":"Notebook Asus","falla":"Teclado defectuoso","estado":"Pendiente","costo":30000},
    {"numero":1008,"cliente":"Agustina Silva","equipo":"PC HP","falla":"Fuente dañada","estado":"En reparación","costo":50000}
]

def mostrar_orden(orden):
    print("\nNúmero:",orden["numero"])
    print("Cliente:",orden["cliente"])
    print("Equipo:",orden["equipo"])
    print("Falla:",orden["falla"])
    print("Estado:",orden["estado"])
    print("Costo:",orden["costo"])

def buscar_orden(numero):
    for orden in ordenes:
        if orden["numero"]==numero:
            return orden
    return None

def filtrar_por_estado(estado):
    cantidad=0

    for orden in ordenes:
        if orden["estado"].lower()==estado.lower():
            mostrar_orden(orden)
            cantidad+=1

    if cantidad==0:
        print("No existen órdenes con ese estado.")

def filtrar_por_costo(limite):
    cantidad=0

    for orden in ordenes:
        if orden["costo"]<=limite:
            mostrar_orden(orden)
            cantidad+=1

    if cantidad==0:
        print("No existen órdenes dentro de ese límite.")

def mostrar_todas():
    for orden in ordenes:
        mostrar_orden(orden)

while True:
    print("\n===== MENÚ =====")
    print("1. Buscar orden")
    print("2. Filtrar por estado")
    print("3. Filtrar por costo")
    print("4. Mostrar todas")
    print("5. Salir")

    opcion=input("Seleccione una opción: ")

    if opcion=="1":
        numero=int(input("Ingrese el número de orden: "))
        orden=buscar_orden(numero)

        if orden is None:
            print("No se encontró la orden.")
        else:
            mostrar_orden(orden)

    elif opcion=="2":
        estado=input("Ingrese el estado: ")
        filtrar_por_estado(estado)

    elif opcion=="3":
        limite=float(input("Ingrese el costo máximo: "))
        filtrar_por_costo(limite)

    elif opcion=="4":
        mostrar_todas()

    elif opcion=="5":
        print("Programa finalizado.")
        break

    else:
        print("Opción inválida.")