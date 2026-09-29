from abc import ABC, abstractmethod

# ==========================================
# EJERCICIO 1: Abstracción, Herencia y Encapsulamiento
# ==========================================


class Persona(ABC):
  """Clase base abstracta que representa a una persona genérica

  con atributos privados y métodos getters para un acceso seguro.
  """

  def __init__(self, nombre, apellido, dni):
    self.__nombre = nombre
    self.__apellido = apellido
    self.__dni = dni

  # Métodos Getters para encapsulamiento seguro
  def get_nombre(self):
    return self.__nombre

  def get_apellido(self):
    return self.__apellido

  def get_dni(self):
    return self.__dni


class Alumno(Persona):
  """Clase Alumno que hereda de Persona, agregando

  atributos específicos como curso y promedio.
  """

  def __init__(self, nombre, apellido, dni, curso, promedio):
    super().__init__(nombre, apellido, dni)
    self.__curso = curso
    self.__promedio = promedio

  # Getters específicos de Alumno
  def get_curso(self):
    return self.__curso

  def get_promedio(self):
    return self.__promedio


# ==========================================
# EJERCICIO 3: Polimorfismo y Estrategias de Guardado
# ==========================================


class EstrategiaGuardado(ABC):
  """Clase base abstracta para definir la interfaz de persistencia."""

  @abstractmethod
  def guardar(self, datos):
    pass


class GuardadoMemoria(EstrategiaGuardado):
  """Estrategia para simular el almacenamiento temporal en memoria RAM."""

  def guardar(self, datos):
    print(
        f" Alumno {datos.get_nombre()} {datos.get_apellido()}"
        " guardado temporalmente."
    )


class GuardadoArchivoTXT(EstrategiaGuardado):
  """Estrategia para realizar la persistencia real escribiendo en un archivo de texto."""

  def guardar(self, datos):
    with open("registro_alumnos.txt", "a", encoding="utf-8") as archivo:
      archivo.write(f"DNI: {datos.get_dni()} | Nombre: {datos.get_nombre()}"f" {datos.get_apellido()} | Curso: {datos.get_curso()} | Promedio:"f" {datos.get_promedio()}\n"
      )
    print(
        f" Alumno {datos.get_nombre()} {datos.get_apellido()}"
        " guardado en 'registro_alumnos.txt'."
    )


# ==========================================
# EJERCICIO 2: El Gestor y la Operación CREATE Segura
# ==========================================


class GestorAcademico:
  """Gestor encargado de administrar las operaciones de creación,

  validando duplicados mediante reglas de negocio e integrando
  inyección de dependencias para el almacenamiento.
  """

  def __init__(self, estrategia_guardado: EstrategiaGuardado):
    self.__base_datos_alumnos = []
    self.__estrategia_guardado = (
        estrategia_guardado  # Inyección de dependencias
    )

  def registrar_nuevo_alumno(self, alumno: Alumno):
    # Regla de negocio: Verificar si el DNI ya existe en la base de datos
    for alumno_existente in self.__base_datos_alumnos:
      if alumno_existente.get_dni() == alumno.get_dni():
        print(
            f" No se pudo registrar. El DNI"
            f" {alumno.get_dni()} ya se encuentra en el sistema."
        )
        return False

    # Si pasa la validación, completamos la operación CREATE
    self.__base_datos_alumnos.append(alumno)
    print(
        f" Alumno {alumno.get_nombre()}"
        f" {alumno.get_apellido()} agregado a la lista interna."
    )

    # Delegamos el guardado final a la estrategia configurada (Polimorfismo)
    self.__estrategia_guardado.guardar(alumno)
    return True

  def obtener_alumnos(self):
    return self.__base_datos_alumnos


# ==========================================
# PRUEBAS / BLOQUE PRINCIPAL
# ==========================================
if __name__ == "__main__":
  # Configuramos la estrategia de guardado (puede cambiarse por GuardadoMemoria() fácilmente)
  estrategia_persistencia = GuardadoArchivoTXT()
  gestor = GestorAcademico(estrategia_persistencia)

  # Instanciación de objetos Alumno (Prueba del Ejercicio 1)
  alumno1 = Alumno("Santiago", "Viluron", "45123456", "5to Año", 9.0)
  alumno2 = Alumno("Lucía", "Martínez", "42987654", "6to Año", 8.5)
  alumno3 = Alumno(
      "Carlos", "Duplicado", "45123456", "4to Año", 7.5
  )  # Mismo DNI que alumno1

  print(" PRUEBA 1: Registro correcto ")
  gestor.registrar_nuevo_alumno(alumno1)

  print("\n PRUEBA 2: Segundo registro correcto ")
  gestor.registrar_nuevo_alumno(alumno2)

  print("\n PRUEBA 3: Intento de registro con DNI duplicado ")
  gestor.registrar_nuevo_alumno(alumno3)