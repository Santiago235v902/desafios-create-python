#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Servo.h>

// ==========================
// ASIGNACIÓN DE PINES
// ==========================
// Nota: Servo.attach() en AVR (Uno/Nano) usa Timer1 vía interrupciones,
// no requiere un pin de PWM por hardware. tone() usa Timer2 por defecto.
// Por lo tanto el pin 6 no evita ningún conflicto de timers con tone();
// se eligió simplemente por comodidad de cableado. (Comentario original
// del código era incorrecto y se corrige aquí para no inducir a error
// en futuras modificaciones.)
const int PIN_SERVO  = 6;
const int PIN_BUZZER = 8;
const int PIN_LED    = 13;

// ==========================
// OBJETOS Y PERIFÉRICOS
// ==========================
LiquidCrystal_I2C lcd(0x27, 16, 2); // Cambiar a 0x3F si la pantalla no enciende
Servo servoPuerta;

// Control de retorno automático a pantalla de inicio tras mostrar el total
unsigned long tiempoMostrarTotal = 0;
bool esperandoRegresoInicio = false;
const unsigned long DURACION_TOTAL_MS = 4000;

// ==========================
// FUNCIONES DE CONTROL DEL SERVO
// ==========================
void moverServo(int angulo) {
  if (!servoPuerta.attached()) {
    servoPuerta.attach(PIN_SERVO);
  }
  servoPuerta.write(angulo);
  delay(500); // Tiempo para completar el movimiento físico
}

void abrirPuerta() {
  moverServo(90); // Ángulo de apertura (ajustar según mecánica)
}

void cerrarPuerta() {
  moverServo(0);  // Ángulo de cierre
}

// ==========================
// FUNCIONES DE SONIDO Y LED
// ==========================
void destellarLED() {
  digitalWrite(PIN_LED, HIGH);
  delay(80);
  digitalWrite(PIN_LED, LOW);
}

void pitarSimple() {
  tone(PIN_BUZZER, 2000, 100);
}

void pitarDoble() {
  tone(PIN_BUZZER, 2000, 80);
  delay(100);
  tone(PIN_BUZZER, 2000, 80);
}

void pitarError() {
  tone(PIN_BUZZER, 400, 300);
}

void melodiaExito() {
  tone(PIN_BUZZER, 1000, 100);
  delay(120);
  tone(PIN_BUZZER, 1500, 100);
  delay(120);
  tone(PIN_BUZZER, 2000, 200);
}

void melodiaSecreta() {
  int notas[] = {523, 659, 784, 1046};
  for (int i = 0; i < 4; i++) {
    tone(PIN_BUZZER, notas[i], 120);
    delay(140);
  }
}

void melodiaCombo10() {
  int notas[] = {784, 784, 988, 1318};
  for (int i = 0; i < 4; i++) {
    tone(PIN_BUZZER, notas[i], 100);
    delay(120);
  }
}

// ==========================
// FUNCIONES DE PANTALLA LCD
// ==========================
void mostrarPantallaInicio() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("  CAJA LISTA    ");
  lcd.setCursor(0, 1);
  lcd.print(" ESCANEE CODIGO ");
  esperandoRegresoInicio = false;
}

void procesarProductoLCD() {
  String datos = Serial.readStringUntil('\n');
  datos.trim();
  int separador = datos.indexOf('|');

  if (separador != -1) {
    String nombre = datos.substring(0, separador);
    String precio = datos.substring(separador + 1);

    if (nombre.length() > 16) {
      nombre = nombre.substring(0, 16);
    }

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print(nombre);

    lcd.setCursor(0, 1);
    lcd.print("Precio: $" + precio);
  }
}

void procesarTotalLCD() {
  String total = Serial.readStringUntil('\n');
  total.trim();

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("TOTAL A PAGAR:  ");
  lcd.setCursor(0, 1);
  lcd.print("$" + total);

  // Programa el regreso automático a la pantalla de inicio
  // (antes el LCD quedaba trabado mostrando el total para siempre)
  tiempoMostrarTotal = millis();
  esperandoRegresoInicio = true;
}

// ==========================
// SETUP Y PRUEBA HARDWARE
// ==========================
void setup() {
  Serial.begin(9600);

  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED, OUTPUT);

  lcd.init();
  lcd.backlight();

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("TEST HARDWARE...");

  abrirPuerta();
  delay(600);
  cerrarPuerta();

  pitarDoble();

  mostrarPantallaInicio();
}

// ==========================
// BUCLE PRINCIPAL
// ==========================
void loop() {
  if (Serial.available() > 0) {
    char comando = Serial.read();

    switch (comando) {
      case 'B': // Inicio
        pitarSimple();
        mostrarPantallaInicio();
        break;

      case 'D': // Beep escaneo
        destellarLED();
        pitarSimple();
        break;

      case 'P': // Recibir Nombre | Precio y mostrar en LCD
        destellarLED();
        pitarSimple();
        procesarProductoLCD();
        break;

      case 'Z': // Combo secreto: 5 productos
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print(" SECRET FOUND! ");
        lcd.setCursor(0, 1);
        lcd.print("  5 PRODUCTOS  ");
        melodiaSecreta();
        break;

      case 'K': // Combo 10 productos (antes colisionaba con 'C' de cerrar puerta)
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("COMBO ALCANZADO!");
        lcd.setCursor(0, 1);
        lcd.print(" 10 PRODUCTOS   ");
        melodiaCombo10();
        break;

      case 'C': // Cerrar puerta (solo acción manual/explícita)
        cerrarPuerta();
        pitarDoble();
        break;

      case 'O': // Abrir puerta
        abrirPuerta();
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print(" PUERTA ABIERTA ");
        pitarSimple();
        break;

      case 'S': // Generación de Ticket / Impresión
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print(" TICKET GENERADO ");
        lcd.setCursor(0, 1);
        lcd.print("  GRACIAS!      ");

        abrirPuerta();
        digitalWrite(PIN_LED, HIGH);
        melodiaExito();
        delay(1200);
        cerrarPuerta();
        digitalWrite(PIN_LED, LOW);
        break;

      case 'T': // Muestra Total del Ticket
        procesarTotalLCD();
        break;

      case 'E': // Producto Eliminado
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("  PRODUCTO      ");
        lcd.setCursor(0, 1);
        lcd.print("  ELIMINADO     ");
        pitarError();
        break;

      case 'X': // Carrito Vacío
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("  CARRITO       ");
        lcd.setCursor(0, 1);
        lcd.print("  VACIO!        ");
        pitarError();
        break;

      case 'Q': // Cierre de aplicación
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print(" CAJA CERRADA   ");
        cerrarPuerta();
        pitarSimple();
        break;
    }
  }

  // Regreso automático a pantalla de inicio tras mostrar el total
  if (esperandoRegresoInicio && (millis() - tiempoMostrarTotal >= DURACION_TOTAL_MS)) {
    mostrarPantallaInicio();
  }
}
