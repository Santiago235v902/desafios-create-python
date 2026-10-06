class Reparacion:
    def __init__(self,orden,cliente,equipo,falla,estado,tecnico,costo_estimado):
        self.orden=orden
        self.cliente=cliente
        self.equipo=equipo
        self.falla=falla
        self.estado=estado
        self.tecnico=tecnico
        self.costo_estimado=costo_estimado

    def mostrar_datos(self):
        print(f"Orden: {self.orden}")
        print(f"Cliente: {self.cliente}")
        print(f"Equipo: {self.equipo}")
        print(f"Falla: {self.falla}")
        print(f"Estado: {self.estado}")
        print(f"Tecnico: {self.tecnico}")
        print(f"Costo estimado: ${self.costo_estimado}")

reparaciones=[
    Reparacion(1,"Santiago","PC","No enciende","Pendiente","Carlos",50000),
    Reparacion(2,"Juan","Notebook","Pantalla rota","En proceso","Maria",80000),
    Reparacion(3,"Lucia","PC","Sistema lento","Finalizada","Carlos",30000),
    Reparacion(4,"Pedro","Impresora","No imprime","Pendiente","Ana",40000),
    Reparacion(5,"Martin","Notebook","No carga","En proceso","Juan",60000),
    Reparacion(6,"Sofia","PC","Falla de disco","Finalizada","Maria",70000),
    Reparacion(7,"Lucas","Monitor","Sin imagen","Pendiente","Ana",35000),
    Reparacion(8,"Carla","Notebook","Teclado roto","Finalizada","Juan",45000),
    Reparacion(9,"Diego","PC","Problema de memoria","En proceso","Carlos",55000),
    Reparacion(10,"Laura","Impresora","Error de conexion","Pendiente","Maria",25000)
]

def buscar_por_orden(numero):
    for reparacion in reparaciones:
        if reparacion.orden==numero:
            return reparacion
    return None

def filtrar_por_estado(estado):
    encontrados=0

    for reparacion in reparaciones:
        if reparacion.estado.lower()==estado.lower():
            reparacion.mostrar_datos()
            print()
            encontrados+=1

    if encontrados==0:
        print("No existen reparaciones con ese estado.")

def filtrar_por_tecnico(tecnico):
    encontrados=0

    for reparacion in reparaciones:
        if reparacion.tecnico.lower()==tecnico.lower():
            reparacion.mostrar_datos()
            print()
            encontrados+=1

    if encontrados==0:
        print("No existen reparaciones asignadas a ese tecnico.")

def filtrar_por_costo(limite):
    encontrados=0

    for reparacion in reparaciones:
        if reparacion.costo_estimado<=limite:
            reparacion.mostrar_datos()
            print()
            encontrados+=1

    if encontrados==0:
        print("No existen reparaciones dentro del costo indicado.")

while True:
    print("\nMENU DE CONSULTAS")
    print("1) Mostrar todas")
    print("2) Buscar por orden")
    print("3) Filtrar por estado")
    print("4) Filtrar por tecnico")
    print("5) Filtrar por costo")
    print("6) Salir")

    opcion=input("Seleccione una opcion: ")

    if opcion=="1":
        for reparacion in reparaciones:
            reparacion.mostrar_datos()
            print()

    elif opcion=="2":
        orden=int(input("Ingrese numero de orden: "))
        reparacion=buscar_por_orden(orden)

        if reparacion:
            reparacion.mostrar_datos()
        else:
            print("Reparacion no encontrada.")

    elif opcion=="3":
        estado=input("Ingrese estado: ")
        filtrar_por_estado(estado)

    elif opcion=="4":
        tecnico=input("Ingrese tecnico: ")
        filtrar_por_tecnico(tecnico)

    elif opcion=="5":
        limite=float(input("Ingrese costo maximo: "))
        filtrar_por_costo(limite)

    elif opcion=="6":
        print("Programa finalizado.")
        break

    else:
        print("Opcion no valida.")