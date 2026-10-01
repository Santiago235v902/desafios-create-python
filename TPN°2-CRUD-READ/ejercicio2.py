repuestos=[
    {"codigo":1001,"descripcion":"SSD Kingston 480 GB","categoria":"Almacenamiento","marca":"Kingston","precio":45000,"stock":8},
    {"codigo":1002,"descripcion":"SSD Crucial 1 TB","categoria":"Almacenamiento","marca":"Crucial","precio":72000,"stock":5},
    {"codigo":1003,"descripcion":"Memoria RAM DDR4 8 GB","categoria":"Memoria","marca":"Kingston","precio":38000,"stock":0},
    {"codigo":1004,"descripcion":"Memoria RAM DDR4 16 GB","categoria":"Memoria","marca":"Corsair","precio":65000,"stock":4},
    {"codigo":1005,"descripcion":"Fuente de alimentación 500W","categoria":"Fuente","marca":"Gamer","precio":55000,"stock":3},
    {"codigo":1006,"descripcion":"Placa de video GTX 1650","categoria":"Video","marca":"MSI","precio":180000,"stock":2},
    {"codigo":1007,"descripcion":"Disco rígido 1 TB","categoria":"Almacenamiento","marca":"Western Digital","precio":60000,"stock":0},
    {"codigo":1008,"descripcion":"Cooler para procesador","categoria":"Refrigeración","marca":"DeepCool","precio":30000,"stock":6}
]

busqueda=input("Ingrese una descripción para buscar: ").lower()
coincidencias=0
disponibles=0

for repuesto in repuestos:
    if busqueda in repuesto["descripcion"].lower():
        coincidencias+=1
        print("\nCódigo:",repuesto["codigo"])
        print("Descripción:",repuesto["descripcion"])
        print("Categoría:",repuesto["categoria"])
        print("Marca:",repuesto["marca"])
        print("Precio:",repuesto["precio"])
        print("Stock:",repuesto["stock"])

        if repuesto["stock"]>0:
            print("Disponible: Sí")
            disponibles+=1
        else:
            print("Disponible: No")

if coincidencias==0:
    print("\nLa búsqueda no produjo resultados.")
else:
    print("\nCantidad de coincidencias:",coincidencias)
    print("Cantidad disponibles:",disponibles)