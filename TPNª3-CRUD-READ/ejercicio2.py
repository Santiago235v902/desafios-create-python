class RecursoDigital:
    def __init__(self,codigo,titulo,categoria,autor,anio,disponible):
        self.codigo=codigo
        self.titulo=titulo
        self.categoria=categoria
        self.autor=autor
        self.anio=anio
        self.disponible=disponible

    def mostrar_resumen(self):
        disponibilidad="Disponible" if self.disponible else "No disponible"
        print(f"Codigo: {self.codigo}")
        print(f"Titulo: {self.titulo}")
        print(f"Categoria: {self.categoria}")
        print(f"Disponibilidad: {disponibilidad}")

recursos=[
    RecursoDigital(1,"Python desde cero","Libro digital","Juan Perez",2024,True),
    RecursoDigital(2,"Introduccion a Python","Tutorial","Ana Lopez",2023,True),
    RecursoDigital(3,"Manual de Java","Manual","Carlos Ruiz",2022,False),
    RecursoDigital(4,"Python avanzado","Libro digital","Maria Gomez",2025,True),
    RecursoDigital(5,"Programacion web","Tutorial","Pedro Diaz",2024,True),
    RecursoDigital(6,"Revista tecnologia","Revista","Laura Sosa",2023,False),
    RecursoDigital(7,"Python para principiantes","Video educativo","Martin Rios",2025,True),
    RecursoDigital(8,"Bases de datos","Manual","Sofia Perez",2022,False),
    RecursoDigital(9,"HTML y CSS","Tutorial","Lucas Torres",2024,True),
    RecursoDigital(10,"Python y algoritmos","Video educativo","Diego Castro",2025,True)
]

busqueda=input("Ingrese una palabra o parte del titulo: ").lower()

coincidencias=0
disponibles=0

print("\nResultados:")

for recurso in recursos:
    if busqueda in recurso.titulo.lower():
        recurso.mostrar_resumen()
        print()
        coincidencias+=1

        if recurso.disponible:
            disponibles+=1

if coincidencias==0:
    print("No existen coincidencias.")
else:
    print(f"Cantidad de coincidencias: {coincidencias}")
    print(f"Cantidad disponibles: {disponibles}")