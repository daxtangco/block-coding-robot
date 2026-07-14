/*
 * ESP32-CAM WiFi Camera Stream
 *
 * Auto-joins the robot arm's AP (any RobotArm-* / robot1234 — no editing needed,
 * works with any arm board) and exposes:
 *   GET /capture  ->  single JPEG snapshot
 *   GET /stream   ->  MJPEG stream (for live preview in Vision tab)
 *
 * Flash with board: AI Thinker ESP32-CAM
 * After flashing: remove GPIO0-GND jumper, press RESET.
 * Open Serial Monitor at 115200 to confirm it found the arm and got 192.168.4.50.
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

// ── WiFi ─────────────────────────────────────────────────────────────────────
// The cam auto-discovers the arm: the arm's SSID is "RobotArm-" + the last bytes
// of its MAC, so it's different on every board. Rather than hardcode one name
// (which breaks the moment you swap arms), the cam scans on boot and joins the
// strongest network whose name starts with this prefix — case-insensitively, so
// it matches "RobotArm-840", "ROBOTARM-840", etc. Zero edits when boards change.
const char* SSID_PREFIX = "robotarm-";   // matched case-insensitively
const char* PASSWORD     = "robot1234";

// Static IP so the camera is ALWAYS at the same address. Without this, the arm's
// DHCP hands out a different IP on each reboot (192.168.4.2, .3, ...) and the
// Vision tab loses the camera. .50 sits above the low range DHCP gives phones/PC,
// so it won't collide. Gateway is the arm AP itself (192.168.4.1).
IPAddress CAM_IP     (192, 168, 4, 50);
IPAddress CAM_GATEWAY(192, 168, 4, 1);
IPAddress CAM_SUBNET (255, 255, 255, 0);

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
    // VGA (640x480) matches YOLOv8's native 640px input — the model sees full
    // detail without upscaling. The AI-Thinker has 4MB PSRAM so we can afford
    // it; use 2 frame buffers for smoother back-to-back captures.
    config.frame_size    = FRAMESIZE_VGA;
    config.jpeg_quality  = 8;    // 0-63, lower = better; 8 is high quality
    config.fb_count      = 2;    // double-buffer needs PSRAM (AI-Thinker has it)
    config.fb_location   = CAMERA_FB_IN_PSRAM;
    config.grab_mode     = CAMERA_GRAB_LATEST;  // always return the freshest frame

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("Camera init failed: 0x%x\n", err);
        return false;
    }

    // OV2640 sensor tuning — applied after init via the sensor API.
    // These make a big difference on the flat-lit desk environment.
    sensor_t* s = esp_camera_sensor_get();
    if (s) {
        s->set_brightness(s,  1);   // +1 brighter (range -2 to +2)
        s->set_contrast(s,    1);   // +1 contrast  (range -2 to +2)
        s->set_saturation(s,  0);   // neutral saturation
        s->set_sharpness(s,   1);   // +1 sharpness
        s->set_denoise(s,     1);   // noise reduction on
        s->set_whitebal(s,    1);   // auto white balance on
        s->set_awb_gain(s,    1);   // AWB gain on
        s->set_exposure_ctrl(s, 1); // auto exposure on
        s->set_aec2(s,        1);   // AEC2 (better exposure algorithm)
        s->set_ae_level(s,    0);   // neutral AE bias
        s->set_gain_ctrl(s,   1);   // auto gain on
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

// ── Find the arm's network ─────────────────────────────────────────────────────
// Scan for access points and return the name of the strongest one whose SSID
// starts with SSID_PREFIX (case-insensitive). Returns "" if none is found, so
// the caller can retry — the arm may still be booting its AP.
String findArmSSID() {
    int n = WiFi.scanNetworks();
    String best = "";
    int bestRSSI = -1000;
    for (int i = 0; i < n; i++) {
        String ssid = WiFi.SSID(i);
        String lower = ssid;
        lower.toLowerCase();
        if (lower.startsWith(SSID_PREFIX) && WiFi.RSSI(i) > bestRSSI) {
            best = ssid;                // keep the AP's real (original-case) name
            bestRSSI = WiFi.RSSI(i);
        }
    }
    WiFi.scanDelete();
    return best;
}

// Connect to the arm AP, discovering its SSID by prefix. Blocks until connected,
// rescanning if the arm isn't up yet. Applies the static IP so the Vision tab
// always finds the cam at 192.168.4.50.
void connectToArm() {
    WiFi.mode(WIFI_STA);
    for (;;) {
        Serial.printf("Scanning for a '%s*' network…\n", SSID_PREFIX);
        String ssid = findArmSSID();
        if (ssid.length() == 0) {
            Serial.println("  no arm AP found — is the arm powered on? retrying in 3s");
            delay(3000);
            continue;
        }
        Serial.printf("Found arm AP: %s — connecting…\n", ssid.c_str());

        if (!WiFi.config(CAM_IP, CAM_GATEWAY, CAM_SUBNET)) {
            Serial.println("Static IP config failed — falling back to DHCP");
        }
        WiFi.begin(ssid.c_str(), PASSWORD);

        // Give this AP ~10s; if it doesn't connect, rescan (arm may have rebooted
        // with a new SSID, or we picked a weak/stale one).
        unsigned long start = millis();
        while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) {
            delay(500);
            Serial.print(".");
        }
        Serial.println();
        if (WiFi.status() == WL_CONNECTED) return;
        Serial.println("  connect timed out — rescanning");
        WiFi.disconnect();
    }
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

    connectToArm();
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
