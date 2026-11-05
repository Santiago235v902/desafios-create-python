#include <Wire.h>
#include <Servo.h>
#include <LiquidCrystal_I2C.h>   // Librería: "LiquidCrystal I2C" de Frank de Brabander

// ==========================
// PINES
// ==========================
const int PIN_SERVO  = 6;
const int PIN_BUZZER = 8;
const int PIN_LED    = 13;

// ==========================
// OBJETOS Y PERIFÉRICOS
// ==========================
LiquidCrystal_I2C lcd(0x27, 16, 2); // Cambiar a 0x3F si la pantalla no enciende
Servo cerradura;

// ==========================
// CONFIGURACIÓN
// ==========================
const long BAUD_RATE          = 9600;  // Debe coincidir con BAUD_ARDUINO en Python
const int  ANGULO_CERRADO     = 0;
const int  ANGULO_ABIERTO     = 90;
const unsigned long T_ABIERTO = 5000;  // ms que el servo permanece abierto
const unsigned long T_MENSAJE = 4000;  // ms que se muestra el mensaje antes de volver al reposo

bool servoAbierto = false;
unsigned long tServo = 0;

bool mensajeActivo = false;
unsigned long tMensaje = 0;

// ==========================
// FUNCIONES AUXILIARES
// ==========================
// Escribe dos líneas de 16 caracteres (rellena con espacios para borrar restos)
void mostrar(const char* linea1, const char* linea2) {
  char buf[17];

  snprintf(buf, sizeof(buf), "%-16s", linea1);
  lcd.setCursor(0, 0);
  lcd.print(buf);

  snprintf(buf, sizeof(buf), "%-16s", linea2);
  lcd.setCursor(0, 1);
  lcd.print(buf);
}

void pantallaReposo() {
  mostrar("Sistema listo", "Escanee un QR...");
  mensajeActivo = false;
}

void beep(int veces, int duracionMs) {
  for (int i = 0; i < veces; i++) {
    tone(PIN_BUZZER, 2000, duracionMs);
    delay(duracionMs + 80);
  }
}

void abrirServo() {
  cerradura.write(ANGULO_ABIERTO);
  digitalWrite(PIN_LED, HIGH);
  servoAbierto = true;
  tServo = millis();
}

void cerrarServo() {
  cerradura.write(ANGULO_CERRADO);
  digitalWrite(PIN_LED, LOW);
  servoAbierto = false;
}

void iniciarMensaje() {
  mensajeActivo = true;
  tMensaje = millis();
}

// ==========================
// SETUP
// ==========================
void setup() {
  Serial.begin(BAUD_RATE);

  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_LED, LOW);

  lcd.init();
  lcd.backlight();
  mostrar("Iniciando...", "");

  cerradura.attach(PIN_SERVO);
  cerrarServo();

  beep(1, 100);
  pantallaReposo();
  Serial.println("Arduino listo");
}

// ==========================
// LOOP
// ==========================
void loop() {
  // --- Comandos desde Python ---
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == 'A') {                       // PRESTAR
      mostrar("PC PRESTADA", "Retire la PC");
      iniciarMensaje();
      abrirServo();
      beep(1, 150);
      Serial.println("OK A");
    } else if (c == 'D') {                // DEVOLVER
      mostrar("PC DEVUELTA", "Deje la PC");
      iniciarMensaje();
      abrirServo();
      beep(2, 100);
      Serial.println("OK D");
    }
    // Cualquier otro byte (\r, \n, etc.) se ignora
  }

  // --- Cierre automático del servo ---
  if (servoAbierto && millis() - tServo >= T_ABIERTO) {
    cerrarServo();
  }

  // --- Volver a la pantalla de reposo ---
  if (mensajeActivo && millis() - tMensaje >= T_MENSAJE) {
    pantallaReposo();
  }
}
