class TicketSoporte:
    def __init__(self,numero,usuario,sector,problema,prioridad,estado):
        self.numero=numero
        self.usuario=usuario
        self.sector=sector
        self.problema=problema
        self.prioridad=prioridad
        self.estado=estado

    def mostrar_datos(self):
        print(f"Numero: {self.numero}")
        print(f"Usuario: {self.usuario}")
        print(f"Sector: {self.sector}")
        print(f"Problema: {self.problema}")
        print(f"Prioridad: {self.prioridad}")
        print(f"Estado: {self.estado}")

tickets=[
    TicketSoporte(1,"Santiago","Administracion","PC no enciende","Alta","Pendiente"),
    TicketSoporte(2,"Juan","Direccion","Impresora no imprime","Media","Resuelto"),
    TicketSoporte(3,"Maria","Laboratorio","Internet lento","Alta","Pendiente"),
    TicketSoporte(4,"Pedro","Biblioteca","No funciona el teclado","Baja","Resuelto"),
    TicketSoporte(5,"Lucia","Secretaria","Error en sistema","Alta","Pendiente"),
    TicketSoporte(6,"Carlos","Informatica","Monitor sin imagen","Media","En proceso"),
    TicketSoporte(7,"Ana","Administracion","Problema con mouse","Baja","Pendiente"),
    TicketSoporte(8,"Martin","Laboratorio","No hay conexion","Alta","Resuelto")
]

def buscar_ticket(numero):
    for ticket in tickets:
        if ticket.numero==numero:
            return ticket
    return None

numero=int(input("Ingrese numero de ticket: "))
ticket=buscar_ticket(numero)

if ticket:
    ticket.mostrar_datos()
else:
    print("Ticket no encontrado")

print("\nTickets pendientes:")
cantidad=0

for ticket in tickets:
    if ticket.estado.lower()=="pendiente":
        ticket.mostrar_datos()
        print()
        cantidad+=1

print(f"Cantidad de tickets pendientes: {cantidad}")