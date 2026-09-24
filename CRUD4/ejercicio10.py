<<<<<<< HEAD
# ==========================================
# TRABAJO PRÁCTICO - OPERACIÓN CREATE
# Registro de equipos de laboratorio
# ==========================================

# 1. Crear la lista vacía para almacenar los registros
equipos = []

# 2. Preguntar cuántos equipos se desean registrar
cantidad = int(input("¿Cuántos equipos desea registrar?: "))

# 3. Utilizar un bucle for para repetir la carga la cantidad de veces indicada
for i in range(cantidad):
    print(f"\n--- Carga de Equipo {i + 1} de {cantidad} ---")
    
    # Solicitar datos del equipo
    inventario = input("Ingrese número de inventario: ")
    tipo = input("Ingrese tipo de equipo (ej. PC, Notebook, Servidor): ")
    marca = input("Ingrese marca: ")
    anio = int(input("Ingrese año de fabricación: "))
    
    # 4. Validar con if/else que el año esté entre 2000 y 2026 inclusive
    if 2000 <= anio <= 2026:
        # Crear el diccionario con los cuatro datos
        nuevo_equipo = {
            "inventario": inventario,
            "tipo": tipo,
            "marca": marca,
            "anio": anio
        }
        
        # 5. Agregar el diccionario a la lista mediante append()
        equipos.append(nuevo_equipo)
        print("¡Éxito! El equipo ha sido registrado correctamente.")
    else:
        # 6. Mostrar mensaje de error si el año no es válido y no guardar
        print("Error: El año ingresado no es válido (debe estar entre 2000 y 2026). Registro descartado.")

# 7. Al finalizar, mostrar la lista completa de equipos creados
print("\n" + "="*40)
print(" LISTA COMPLETA DE EQUIPOS REGISTRADOS ")
print("="*40)

if len(equipos) > 0:
    for equipo in equipos:
        print(f"Inventario: {equipo['inventario']} | Tipo: {equipo['tipo']} | Marca: {equipo['marca']} | Año: {equipo['anio']}")
else:
    print("No se registraron equipos válidos.")
=======
# ==========================================
# TRABAJO PRÁCTICO - OPERACIÓN CREATE
# Registro de equipos de laboratorio
# ==========================================

# 1. Crear la lista vacía para almacenar los registros
equipos = []

# 2. Preguntar cuántos equipos se desean registrar
cantidad = int(input("¿Cuántos equipos desea registrar?: "))

# 3. Utilizar un bucle for para repetir la carga la cantidad de veces indicada
for i in range(cantidad):
    print(f"\n--- Carga de Equipo {i + 1} de {cantidad} ---")
    
    # Solicitar datos del equipo
    inventario = input("Ingrese número de inventario: ")
    tipo = input("Ingrese tipo de equipo (ej. PC, Notebook, Servidor): ")
    marca = input("Ingrese marca: ")
    anio = int(input("Ingrese año de fabricación: "))
    
    # 4. Validar con if/else que el año esté entre 2000 y 2026 inclusive
    if 2000 <= anio <= 2026:
        # Crear el diccionario con los cuatro datos
        nuevo_equipo = {
            "inventario": inventario,
            "tipo": tipo,
            "marca": marca,
            "anio": anio
        }
        
        # 5. Agregar el diccionario a la lista mediante append()
        equipos.append(nuevo_equipo)
        print("¡Éxito! El equipo ha sido registrado correctamente.")
    else:
        # 6. Mostrar mensaje de error si el año no es válido y no guardar
        print("Error: El año ingresado no es válido (debe estar entre 2000 y 2026). Registro descartado.")

# 7. Al finalizar, mostrar la lista completa de equipos creados
print("\n" + "="*40)
print(" LISTA COMPLETA DE EQUIPOS REGISTRADOS ")
print("="*40)

if len(equipos) > 0:
    for equipo in equipos:
        print(f"Inventario: {equipo['inventario']} | Tipo: {equipo['tipo']} | Marca: {equipo['marca']} | Año: {equipo['anio']}")
else:
    print("No se registraron equipos válidos.")
>>>>>>> 77ab13a377bbad5c616cd57d66bf8bde3bb556b5
