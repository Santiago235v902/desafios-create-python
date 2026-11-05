#include "esp_camera.h"

#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

#define FLASH_GPIO_NUM     4  // LED flash de la ESP32-CAM

// DEBE coincidir con BAUD_ESP en el Python. Si tu adaptador lo soporta, prueba 2000000.
#define BAUD_RATE 921600

void setup() {
  Serial.begin(BAUD_RATE);

  pinMode(FLASH_GPIO_NUM, OUTPUT);
  digitalWrite(FLASH_GPIO_NUM, LOW);

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if (psramFound()) {
    config.frame_size = FRAMESIZE_VGA;           // 640x480
    config.jpeg_quality = 12;                    // 10 = más nítido pero más pesado por serial
    config.fb_count = 2;                         // con 2 buffers, GRAB_LATEST sí entrega el frame más nuevo
    config.fb_location = CAMERA_FB_IN_PSRAM;
    config.grab_mode = CAMERA_GRAB_LATEST;
  } else {
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 15;
    config.fb_count = 1;
    config.fb_location = CAMERA_FB_IN_DRAM;
    config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    // Si la cámara falla, reiniciar en lugar de quedarse mudo para siempre
    delay(1000);
    ESP.restart();
  }
}

void loop() {
  // --- Órdenes desde Python: leer TODO lo pendiente ---
  while (Serial.available() > 0) {
    char comando = Serial.read();
    if (comando == '1') {
      digitalWrite(FLASH_GPIO_NUM, HIGH);
    } else if (comando == '0') {
      digitalWrite(FLASH_GPIO_NUM, LOW);
    }
  }

  // --- Capturar y enviar fotograma ---
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    delay(10);
    return;
  }

  // Cabecera propia (AA 55 AA 55) + longitud uint32 little-endian.
  // Ya no se confunde con el FF D8 interno del JPEG.
  uint32_t len = fb->len;
  uint8_t header[8] = {
    0xAA, 0x55, 0xAA, 0x55,
    (uint8_t)(len & 0xFF),
    (uint8_t)((len >> 8) & 0xFF),
    (uint8_t)((len >> 16) & 0xFF),
    (uint8_t)((len >> 24) & 0xFF)
  };
  Serial.write(header, 8);
  Serial.write(fb->buf, len);

  esp_camera_fb_return(fb);
}
