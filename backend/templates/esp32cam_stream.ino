/*
 * ESP32-CAM WiFi Camera Stream
 *
 * Connects to the robot arm's AP (RobotArm-XXXX / robot1234) and exposes:
 *   GET /capture  ->  single JPEG snapshot
 *   GET /stream   ->  MJPEG stream (for live preview in Vision tab)
 *
 * Flash with board: AI Thinker ESP32-CAM
 * After flashing: remove GPIO0-GND jumper, press RESET.
 * Open Serial Monitor at 115200 to see the assigned IP address.
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

// ── WiFi ─────────────────────────────────────────────────────────────────────
// Connect to the arm's access point.
const char* SSID     = "RobotArm-XXXX";   // change XXXX to your arm's suffix
const char* PASSWORD = "robot1234";

// ── Camera pins (AI-Thinker ESP32-CAM) ───────────────────────────────────────
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

WebServer server(80);

// ── Camera init ───────────────────────────────────────────────────────────────
bool initCamera() {
    camera_config_t config;
    config.ledc_channel  = LEDC_CHANNEL_0;
    config.ledc_timer    = LEDC_TIMER_0;
    config.pin_d0        = Y2_GPIO_NUM;
    config.pin_d1        = Y3_GPIO_NUM;
    config.pin_d2        = Y4_GPIO_NUM;
    config.pin_d3        = Y5_GPIO_NUM;
    config.pin_d4        = Y6_GPIO_NUM;
    config.pin_d5        = Y7_GPIO_NUM;
    config.pin_d6        = Y8_GPIO_NUM;
    config.pin_d7        = Y9_GPIO_NUM;
    config.pin_xclk      = XCLK_GPIO_NUM;
    config.pin_pclk      = PCLK_GPIO_NUM;
    config.pin_vsync     = VSYNC_GPIO_NUM;
    config.pin_href      = HREF_GPIO_NUM;
    config.pin_sscb_sda  = SIOD_GPIO_NUM;
    config.pin_sscb_scl  = SIOC_GPIO_NUM;
    config.pin_pwdn      = PWDN_GPIO_NUM;
    config.pin_reset     = RESET_GPIO_NUM;
    config.xclk_freq_hz  = 20000000;
    config.pixel_format  = PIXFORMAT_JPEG;
    config.frame_size    = FRAMESIZE_QVGA;   // 320x240 — good for detection
    config.jpeg_quality  = 12;               // 0-63, lower = better quality
    config.fb_count      = 1;

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("Camera init failed: 0x%x\n", err);
        return false;
    }
    return true;
}

// ── GET /capture — single JPEG ────────────────────────────────────────────────
void handleCapture() {
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
        server.send(503, "text/plain", "Camera capture failed");
        return;
    }
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.sendHeader("Cache-Control", "no-cache");
    server.send_P(200, "image/jpeg", (const char*)fb->buf, fb->len);
    esp_camera_fb_return(fb);
}

// ── GET /stream — MJPEG stream ────────────────────────────────────────────────
void handleStream() {
    WiFiClient client = server.client();

    // Send multipart header
    String header =
        "HTTP/1.1 200 OK\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n";
    client.print(header);

    while (client.connected()) {
        camera_fb_t* fb = esp_camera_fb_get();
        if (!fb) { delay(100); continue; }

        client.print("--frame\r\n");
        client.print("Content-Type: image/jpeg\r\n");
        client.printf("Content-Length: %u\r\n\r\n", fb->len);
        client.write(fb->buf, fb->len);
        client.print("\r\n");
        esp_camera_fb_return(fb);

        delay(50);   // ~20 fps max; the backend polls /capture anyway
    }
}

void handleNotFound() {
    server.send(404, "text/plain", "Not found");
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    Serial.println("\nESP32-CAM starting...");

    if (!initCamera()) {
        Serial.println("Camera init failed — check module seating");
        return;
    }
    Serial.println("Camera OK");

    WiFi.mode(WIFI_STA);
    WiFi.begin(SSID, PASSWORD);
    Serial.printf("Connecting to %s", SSID);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println();
    Serial.printf("Connected! IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.println("Endpoints:");
    Serial.printf("  Snapshot : http://%s/capture\n", WiFi.localIP().toString().c_str());
    Serial.printf("  Stream   : http://%s/stream\n",  WiFi.localIP().toString().c_str());

    server.on("/capture", HTTP_GET, handleCapture);
    server.on("/stream",  HTTP_GET, handleStream);
    server.onNotFound(handleNotFound);
    server.begin();
    Serial.println("Web server started.");
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
    server.handleClient();
}
