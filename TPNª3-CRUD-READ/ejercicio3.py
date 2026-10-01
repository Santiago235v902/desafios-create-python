class Componente:
    def __init__(self,codigo,nombre,tipo,marca,stock,ubicacion):
        self.codigo=codigo
        self.nombre=nombre
        self.tipo=tipo
        self.marca=marca
        self.stock=stock
        self.ubicacion=ubicacion

    def hay_stock(self):
        return self.stock>0

    def mostrar_datos(self):
        print(f"Codigo: {self.codigo}")
        print(f"Nombre: {self.nombre}")
        print(f"Tipo: {self.tipo}")
        print(f"Marca: {self.marca}")
        print(f"Stock: {self.stock}")
        print(f"Ubicacion: {self.ubicacion}")

componentes=[
    Componente(1,"Arduino UNO","Placa","Arduino",15,"Estante A"),
    Componente(2,"Arduino Nano","Placa","Arduino",8,"Estante A"),
    Componente(3,"ESP32","Placa","Espressif",12,"Estante B"),
    Componente(4,"Resistencia 220 Ohm","Resistencia","Vishay",50,"Estante C"),
    Componente(5,"Resistencia 1K Ohm","Resistencia","Vishay",30,"Estante C"),
    Componente(6,"LED rojo","LED","Kingbright",40,"Estante D"),
    Componente(7,"LED azul","LED","Kingbright",25,"Estante D"),
    Componente(8,"Sensor ultrasonico","Sensor","HC-SR04",6,"Estante E"),
    Componente(9,"Sensor de luz","Sensor","LDR",18,"Estante E"),
    Componente(10,"Motor DC","Motor","Mabuchi",10,"Estante F")
]

tipo=input("Ingrese tipo de componente: ").lower()
minimo=int(input("Ingrese stock minimo: "))

cantidad=0
mayor=None

print("\nResultados:")

for componente in componentes:
    if componente.tipo.lower()==tipo and componente.stock>=minimo:
        componente.mostrar_datos()
        print()
        cantidad+=1

        if mayor is None or componente.stock>mayor.stock:
            mayor=componente

if cantidad==0:
    print("No existen componentes que cumplan las condiciones.")
else:
    print(f"Cantidad de componentes: {cantidad}")
    print("\nComponente con mayor stock:")
    mayor.mostrar_datos()