alumnos=[
    {"nombre":"Santiago","curso":"4°3°","promedio":8.5,"trabajos":9},
    {"nombre":"Alexander","curso":"4°3°","promedio":6.5,"trabajos":8},
    {"nombre":"Molina","curso":"4°3°","promedio":9.2,"trabajos":10},
    {"nombre":"Valentin","curso":"4°3°","promedio":7.8,"trabajos":7},
    {"nombre":"Salinas","curso":"4°3°","promedio":5.9,"trabajos":6},
    {"nombre":"Juan","curso":"4°3°","promedio":8.8,"trabajos":9},
    {"nombre":"Camila","curso":"4°3°","promedio":7.2,"trabajos":8},
    {"nombre":"Nicolás","curso":"4°3°","promedio":9.5,"trabajos":10},
    {"nombre":"Agustina","curso":"4°3°","promedio":6.8,"trabajos":5},
    {"nombre":"Franco","curso":"4°3°","promedio":8.1,"trabajos":8}
]

promedio_minimo=float(input("Ingrese el promedio mínimo: "))
trabajos_minimos=int(input("Ingrese la cantidad mínima de trabajos: "))

cumplen=0
no_cumplen=0
mejor_promedio=-1
mejor_alumno=""

for alumno in alumnos:
    if alumno["promedio"]>=promedio_minimo and alumno["trabajos"]>=trabajos_minimos:
        print("\nNombre:",alumno["nombre"])
        print("Curso:",alumno["curso"])
        print("Promedio:",alumno["promedio"])
        print("Trabajos:",alumno["trabajos"])

        cumplen+=1

        if alumno["promedio"]>mejor_promedio:
            mejor_promedio=alumno["promedio"]
            mejor_alumno=alumno["nombre"]
    else:
        no_cumplen+=1

print("\nCantidad que cumple:",cumplen)
print("Cantidad que no cumple:",no_cumplen)

if cumplen==0:
    print("Ningún alumno cumple las condiciones.")
else:
    print("Mejor promedio:",mejor_alumno,"-",mejor_promedio)