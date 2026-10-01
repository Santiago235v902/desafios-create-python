equipos=[
    {"inventario":1001,"tipo":"PC","marca":"Lenovo","estado":"Disponible","anio":2023},
    {"inventario":1002,"tipo":"Notebook","marca":"HP","estado":"En reparación","anio":2022},
    {"inventario":1003,"tipo":"PC","marca":"Dell","estado":"Disponible","anio":2024},
    {"inventario":1004,"tipo":"Monitor","marca":"Samsung","estado":"Baja","anio":2020},
    {"inventario":1005,"tipo":"Notebook","marca":"Lenovo","estado":"Disponible","anio":2025},
    {"inventario":1006,"tipo":"PC","marca":"Asus","estado":"Disponible","anio":2021},
    {"inventario":1007,"tipo":"Monitor","marca":"LG","estado":"En reparación","anio":2023},
    {"inventario":1008,"tipo":"Notebook","marca":"Acer","estado":"Disponible","anio":2024}
]

anio_minimo=int(input("Ingrese el año mínimo: "))
cantidad=0

for equipo in equipos:
    if equipo["estado"]=="Disponible" and equipo["anio"]>=anio_minimo:
        print("\nInventario:",equipo["inventario"])
        print("Tipo:",equipo["tipo"])
        print("Marca:",equipo["marca"])
        print("Estado:",equipo["estado"])
        print("Año:",equipo["anio"])
        cantidad+=1

if cantidad==0:
    print("\nNo existe ningún equipo que cumpla las condiciones.")
else:
    print("\nCantidad de equipos:",cantidad)