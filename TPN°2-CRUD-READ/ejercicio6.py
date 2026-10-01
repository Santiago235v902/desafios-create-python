class DispositivoRed:
    def __init__(self,codigo,tipo,marca,velocidad_mbps,precio,stock):
        self.codigo=codigo
        self.tipo=tipo
        self.marca=marca
        self.velocidad_mbps=velocidad_mbps
        self.precio=precio
        self.stock=stock

    def mostrar_datos(self):
        print("\nCódigo:",self.codigo)
        print("Tipo:",self.tipo)
        print("Marca:",self.marca)
        print("Velocidad:",self.velocidad_mbps,"Mbps")
        print("Precio:",self.precio)
        print("Stock:",self.stock)

    def hay_stock(self):
        return self.stock>0

dispositivos=[
    DispositivoRed(1001,"Router","TP-Link",1000,85000,5),
    DispositivoRed(1002,"Switch","TP-Link",1000,65000,3),
    DispositivoRed(1003,"Access Point","Ubiquiti",1200,150000,2),
    DispositivoRed(1004,"Router","MikroTik",2500,210000,1),
    DispositivoRed(1005,"Switch","Cisco",1000,180000,0),
    DispositivoRed(1006,"Access Point","TP-Link",3000,190000,4)
]

def buscar_por_velocidad(velocidad):
    cantidad=0

    for dispositivo in dispositivos:
        if dispositivo.velocidad_mbps>=velocidad and dispositivo.hay_stock():
            dispositivo.mostrar_datos()
            cantidad+=1

    if cantidad==0:
        print("No existen dispositivos que cumplan las condiciones.")

def buscar_por_codigo(codigo):
    for dispositivo in dispositivos:
        if dispositivo.codigo==codigo:
            return dispositivo
    return None

def buscar_por_presupuesto(presupuesto):
    cantidad=0

    for dispositivo in dispositivos:
        if dispositivo.hay_stock() and dispositivo.precio<=presupuesto:
            dispositivo.mostrar_datos()
            cantidad+=1

    if cantidad==0:
        print("No existen dispositivos dentro del presupuesto.")

while True:
    print("\n===== MENÚ =====")
    print("1. Buscar por velocidad")
    print("2. Buscar por código")
    print("3. Buscar por presupuesto")
    print("4. Mostrar todos")
    print("5. Salir")

    opcion=input("Seleccione una opción: ")

    if opcion=="1":
        velocidad=int(input("Ingrese la velocidad mínima: "))
        buscar_por_velocidad(velocidad)

    elif opcion=="2":
        codigo=int(input("Ingrese el código: "))
        dispositivo=buscar_por_codigo(codigo)

        if dispositivo is None:
            print("No se encontró el dispositivo.")
        else:
            dispositivo.mostrar_datos()

    elif opcion=="3":
        presupuesto=float(input("Ingrese el presupuesto máximo: "))
        buscar_por_presupuesto(presupuesto)

    elif opcion=="4":
        for dispositivo in dispositivos:
            dispositivo.mostrar_datos()

    elif opcion=="5":
        print("Programa finalizado.")
        break

    else:
        print("Opción inválida.")