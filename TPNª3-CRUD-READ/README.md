# Cierre – Análisis de READ con POO

## 1. ¿Qué representa cada objeto dentro de estos sistemas?

Cada objeto representa un registro concreto del sistema. Por ejemplo, un objeto `TicketSoporte` representa un ticket de soporte específico.

## 2. ¿Qué diferencia existe entre buscar un único objeto y filtrar varios objetos?

Una búsqueda busca un objeto específico y devuelve ese objeto o `None`. Un filtro recorre todos los objetos y muestra los que cumplen una determinada condición.

## 3. ¿Qué ventaja aporta `return` cuando se busca un objeto por código, número u orden?

Permite devolver directamente el objeto encontrado para poder utilizar sus datos fuera de la función. Si no existe, permite devolver `None`.

## 4. ¿Qué función cumple una lista de objetos durante una operación READ?

La lista almacena todos los objetos y permite recorrerlos para realizar búsquedas, filtros y consultas.

## 5. ¿Qué ventaja tiene colocar ciertas consultas dentro de métodos de la clase?

Permite que cada objeto tenga comportamientos relacionados con sus propios datos y evita repetir la misma lógica fuera de la clase.

## 6. ¿Por qué los ejercicios realizados siguen siendo READ aunque utilicen clases, métodos, funciones, `for` e `if`?

Porque todas las operaciones solamente consultan, buscan, filtran, comparan o muestran información. Ninguna modifica ni elimina los objetos.

## 7. ¿Qué diferencia observás entre consultar registros representados con diccionarios y consultar objetos?

Con diccionarios se accede principalmente mediante claves, mientras que con objetos se utilizan atributos y métodos. Los objetos permiten además asociar comportamientos directamente con los datos.
