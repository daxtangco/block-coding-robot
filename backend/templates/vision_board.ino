/*
 * ESP32-CAM Vision Board Firmware
 * Runs TFLite Micro inference, publishes to Blynk V10/V11
 */

#define BLYNK_TEMPLATE_ID "{{BLYNK_TEMPLATE_ID}}"
#define BLYNK_TEMPLATE_NAME "{{BLYNK_TEMPLATE_NAME}}"
#define BLYNK_AUTH_TOKEN "{{BLYNK_AUTH_TOKEN}}"

#include <WiFi.h>
#include <BlynkSimpleEsp32.h>
#include "esp_camera.h"

// WiFi credentials
char ssid[] = "{{WIFI_SSID}}";
char pass[] = "{{WIFI_PASSWORD}}";

// Camera pins (AI-Thinker ESP32-CAM)
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

// Mock inference (replace with TFLite Micro in week 1)
String mockInference() {
  // Placeholder: returns random class for now
  const char* classes[] = {"red_small", "blue_small", "red_large", "blue_large", "none"};
  return classes[random(0, 5)];
}

int mockConfidence() {
  return random(70, 95);  // 70-95% confidence
}

void setup() {
  Serial.begin(115200);

  // Initialize camera
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
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA;  // 320x240
  config.jpeg_quality = 12;
  config.fb_count = 1;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", err);
    return;
  }

  // Connect to Blynk
  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);
  Serial.println("Vision board ready");
}

void loop() {
  Blynk.run();

  // Capture frame and run inference every 1 second
  static unsigned long lastInference = 0;
  if (millis() - lastInference > 1000) {
    lastInference = millis();

    // TODO: Replace with real TFLite Micro inference
    String detectedClass = mockInference();
    int confidence = mockConfidence();

    // Publish to Blynk
    Blynk.virtualWrite(V10, detectedClass);
    Blynk.virtualWrite(V11, confidence);

    Serial.printf("Detection: %s (%d%%)\n", detectedClass.c_str(), confidence);
  }
}
