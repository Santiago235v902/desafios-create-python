class Videojuego:
    def __init__(self,codigo,titulo,genero,plataforma,anio,horas_estimadas):
        self.codigo=codigo
        self.titulo=titulo
        self.genero=genero
        self.plataforma=plataforma
        self.anio=anio
        self.horas_estimadas=horas_estimadas

    def mostrar_datos(self):
        print(f"Codigo: {self.codigo}")
        print(f"Titulo: {self.titulo}")
        print(f"Genero: {self.genero}")
        print(f"Plataforma: {self.plataforma}")
        print(f"Anio: {self.anio}")
        print(f"Horas estimadas: {self.horas_estimadas}")

    def es_del_genero(self,genero):
        return self.genero.lower()==genero.lower()

    def supera_horas(self,cantidad):
        return self.horas_estimadas>cantidad

videojuegos=[
    Videojuego(1,"Minecraft","Supervivencia","PC",2011,80),
    Videojuego(2,"FIFA 26","Deportes","PC",2025,50),
    Videojuego(3,"GTA V","Accion","PC",2013,70),
    Videojuego(4,"Portal 2","Puzzle","PC",2011,10),
    Videojuego(5,"The Witcher 3","RPG","PC",2015,100),
    Videojuego(6,"Fortnite","Accion","PC",2017,60),
    Videojuego(7,"Stardew Valley","Simulacion","PC",2016,50),
    Videojuego(8,"Hollow Knight","Aventura","PC",2017,30)
]

genero=input("Ingrese genero: ")
encontrados=0

print("\nVideojuegos del genero:")

for juego in videojuegos:
    if juego.es_del_genero(genero):
        juego.mostrar_datos()
        print()
        encontrados+=1

if encontrados==0:
    print("No existen videojuegos de ese genero.")

horas=float(input("\nIngrese cantidad de horas: "))
encontrados=0

print("\nVideojuegos que superan esa cantidad de horas:")

for juego in videojuegos:
    if juego.supera_horas(horas):
        juego.mostrar_datos()
        print()
        encontrados+=1

if encontrados==0:
    print("No existen videojuegos que superen esa cantidad de horas.")

def buscar_por_codigo(codigo):
    for juego in videojuegos:
        if juego.codigo==codigo:
            return juego
    return None

codigo=int(input("\nIngrese codigo del videojuego: "))
juego=buscar_por_codigo(codigo)

if juego:
    juego.mostrar_datos()
else:
    print("Videojuego no encontrado.")