# ESP32 Access Point + PWA Controller Design

**Date:** 2026-06-04  
**Status:** Approved  
**Goal:** Replace Blynk cloud dependency with local ESP32 Access Point and Progressive Web App for robot control

## Problem Statement

Current system requires:
- External WiFi network with 2.4GHz support
- Blynk cloud account setup (template ID, auth token)
- Mobile hotspot configuration for testing
- Complex troubleshooting when WiFi/Blynk connectivity fails

This creates barriers for students and instructors, especially in environments with restricted WiFi or no internet access.

## Solution Overview

Transform the ESP32 into a WiFi Access Point that serves a Progressive Web App (PWA) for mobile control. Students connect their phones directly to the robot's WiFi network and control it via a browser-based interface. No external WiFi, no cloud services, no app stores.

## Architecture

### System Components

1. **ESP32 Firmware** - Runs as WiFi Access Point with WebSocket server, controls servos via PCA9685
2. **Progressive Web App (PWA)** - Mobile-optimized control interface served by ESP32
3. **Desktop IDE** - Existing laptop web interface for block programming (unchanged)
4. **Flash Workflow** - USB-based firmware upload via esptool (unchanged)

### Network Topology

```
Student's Phone <--WiFi--> ESP32 Access Point <--I2C--> PCA9685 <---> 5 Servos
                              |
                           USB Cable
                              |
                    Student's Laptop (for flashing only)
```

### Key Changes

**Remove:**
- Blynk cloud integration
- External WiFi requirement
- Blynk mobile app dependency
- WiFi credentials in firmware
- Blynk Setup tab in IDE

**Add:**
- ESP32 AP mode configuration
- WebSocket server for real-time control
- Embedded PWA files (HTML/CSS/JS)
- Captive portal for easy access
- SPIFFS filesystem for serving web files

**Keep:**
- Desktop IDE for block programming
- USB flashing workflow via esptool
- PCA9685 servo control
- Block programming and pose teaching
- arduino-cli build system

## ESP32 Firmware Design

### Access Point Configuration

```cpp
// Access Point settings
SSID: "RobotArm-XXXX"  // XXXX = last 4 MAC digits for uniqueness
Password: "robot1234"   // Simple, student-friendly, configurable
IP Address: 192.168.4.1 // Standard AP gateway
Channel: 6              // 2.4GHz, good compatibility
```

**Why these settings:**
- Unique SSID prevents conflicts in classroom with multiple robots
- Simple password is easy to remember and type
- Standard IP makes documentation consistent
- Channel 6 avoids most common congestion

### WebSocket Server

- **Library:** `ESPAsyncWebServer` + `AsyncWebSocket` (stable, widely used)
- **Port:** 80 (standard HTTP/WebSocket)
- **Endpoint:** `/ws`
- **Concurrent clients:** Multiple (teacher + students can connect simultaneously)

### Communication Protocol

**Message Format:** JSON over WebSocket

**Phone → ESP32 Messages:**

```json
// Set servo angle
{
  "type": "servo",
  "channel": 0,     // 0-4 for servos
  "angle": 90       // 0-180 degrees
}

// Toggle auto/manual mode
{
  "type": "mode",
  "auto": true      // true = auto mode, false = manual mode
}

// Reset all servos to defaults
{
  "type": "reset"
}
```

**ESP32 → Phone Messages:**

```json
// Current state (sent on connect and after any change)
{
  "type": "state",
  "servos": [0, 60, 70, 60, 90],  // Current angles for 5 servos
  "auto": false                     // Current mode
}
```

**Why JSON:**
- Human-readable for debugging
- Standard parsing libraries on both sides
- Extensible for future features
- Lightweight enough for real-time control

### Captive Portal

When a phone connects to `RobotArm-XXXX`, the ESP32 responds to DNS queries and HTTP requests to automatically open the browser to `192.168.4.1`.

**Implementation:**
- DNSServer redirects all domains to ESP32 IP
- HTTP handler serves PWA on all paths
- Works on iOS and Android
- Student never needs to manually type IP address

### File Storage (SPIFFS)

- **Filesystem:** SPIFFS (SPI Flash File System)
- **Files stored:** HTML, CSS, JavaScript for PWA (~50KB total)
- **Available space:** ESP32 has 4MB flash, plenty of room
- **Served via:** ESPAsyncWebServer static file handler

**File structure:**
```
/data/
  index.html      # Main PWA page
  style.css       # Mobile-optimized styles
  app.js          # WebSocket client + UI logic
  manifest.json   # PWA manifest for "Add to Home Screen"
  icon-192.png    # PWA icon
  icon-512.png    # PWA icon
```

### Servo Control

**No changes** to PCA9685 control logic:
- Same I2C communication (GPIO 21 SDA, GPIO 22 SCL)
- Same pulse width mapping (150-600 for 0-180°)
- Same default positions (Base=0, Shoulder=60, Elbow=70, Wrist=60, Gripper=90)
- Same channels (0=Base, 1=Shoulder, 2=Elbow, 3=Wrist, 4=Gripper)

### Auto Mode

When auto mode is enabled via PWA:
- ESP32 ignores incoming servo commands from WebSocket
- Runs `runStudentProgram()` function (contains block-generated code)
- Manual control re-enabled when auto mode toggled off

## Progressive Web App Design

### User Interface

**Target devices:** Mobile phones (320px - 428px width)  
**Orientation:** Portrait (vertical)  
**Theme:** Dark (reduces eye strain, modern aesthetic)  
**Touch targets:** Minimum 44px (iOS Human Interface Guidelines)

### Layout

```
┌─────────────────────────┐
│   🤖 Robot Arm Control  │  ← Header with title
├─────────────────────────┤
│ Connection: Connected ●  │  ← Status indicator (green = connected)
├─────────────────────────┤
│                         │
│  Base        [====●---] │  ← Servo slider + real-time value
│  0°          90°    180°│     Labels at min/current/max
│                         │
│  Shoulder    [==●-----] │
│  0°          60°    180°│
│                         │
│  Elbow       [==●-----] │
│  0°          70°    180°│
│                         │
│  Wrist       [==●-----] │
│  0°          60°    180°│
│                         │
│  Gripper     [====●---] │
│  0°          90°    180°│
│                         │
├─────────────────────────┤
│                         │
│  Mode:  [Manual] [Auto] │  ← Toggle buttons (one active)
│                         │
│  [ 🔄 Reset Defaults ] │  ← Full-width action button
│                         │
└─────────────────────────┘
```

### PWA Features

**manifest.json:**
```json
{
  "name": "Robot Arm Controller",
  "short_name": "Robot",
  "start_url": "/",
  "display": "standalone",
  "theme_color": "#1a1a1a",
  "background_color": "#1a1a1a",
  "icons": [
    {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}
  ]
}
```

**Service Worker:**
- Caches static files (HTML/CSS/JS/images)
- Provides offline fallback page
- Instant loading on repeat visits
- Progressive enhancement (works without it too)

**Why PWA:**
- No app store submission required
- Works on iOS and Android from same code
- "Add to Home Screen" creates app-like experience
- Updates instantly (no app store review delay)
- Can be used immediately via browser

### WebSocket Connection Logic

**On page load:**
1. Attempt WebSocket connection to `ws://192.168.4.1/ws`
2. Display "Connecting..." status
3. On success: Request current state, enable controls
4. On failure: Show "Disconnected" error, disable controls

**Auto-reconnect:**
- If connection drops, retry every 2 seconds
- Visual feedback (connection status indicator)
- Controls greyed out when disconnected
- Re-sync state on reconnection

**State synchronization:**
- On connect: ESP32 sends current servo angles and mode
- PWA updates all sliders to match robot state
- Prevents "jump" when slider positions don't match reality

### Interaction Flow

1. **Student moves slider:**
   - JavaScript captures `input` event
   - Sends `{"type": "servo", "channel": X, "angle": Y}` immediately
   - Updates local UI (no wait for response)

2. **ESP32 receives command:**
   - Parses JSON message
   - Updates PCA9685 servo via I2C
   - Broadcasts state to all connected clients

3. **PWA receives state:**
   - Updates slider if different (handles multi-client sync)
   - Provides visual confirmation

**Total latency:** ~50ms (imperceptible to user)

### Error Handling

| Error | Behavior | Recovery |
|-------|----------|----------|
| WebSocket disconnect | Show "Disconnected" banner, grey out controls | Auto-reconnect every 2s |
| Invalid command | ESP32 logs error (USB serial), ignores command | User tries again |
| Multiple clients | Last command wins, state broadcast to all | Natural collaborative behavior |
| Phone loses WiFi | Connection drops, auto-reconnect | Re-establish when back in range |

## Desktop IDE Changes

### Setup Tab Modifications

**Remove:**
- WiFi SSID input field
- WiFi Password input field
- Blynk Template ID input field
- Blynk Template Name input field
- Blynk Auth Token input field

**Add:**
- Informational panel explaining AP mode
- Instructions: "Connect your phone to RobotArm-XXXX WiFi to control"
- AP configuration settings (optional):
  - Custom SSID (default: RobotArm-XXXX)
  - Custom password (default: robot1234)

**Keep:**
- Save Settings button
- Build & Flash button
- Status messages

### Remove Blynk Setup Tab

The entire "Blynk Setup" tab is removed from the navigation. The guide is no longer needed since there's no cloud service to configure.

### Build Process

**No changes** to compilation:
- Still uses arduino-cli
- Still targets esp32:esp32:esp32
- Still outputs .bin file
- Still uploads via esptool

**Template changes:**
- Remove `#include <BlynkSimpleEsp32.h>`
- Remove Blynk virtual pin handlers (BLYNK_WRITE)
- Remove Blynk.begin() and Blynk.run()
- Add WebSocket server setup
- Add Access Point configuration
- Add SPIFFS initialization

## Student Workflow

### Initial Setup (One-time, with Laptop)

1. Student receives ESP32 + robot hardware
2. Plugs ESP32 into laptop via USB cable
3. Opens Desktop IDE in browser (localhost:8000)
4. Goes to Setup tab (no configuration needed)
5. Clicks "Build & Flash"
6. Firmware compiles and uploads via USB
7. ESP32 boots up as Access Point (LED indicates ready)

**Time:** ~2 minutes (mostly compilation)  
**Complexity:** Minimal (just plug in and click)

### Daily Programming Workflow (Laptop)

1. Open Desktop IDE
2. **Program tab:** Drag blocks to create robot program
3. **Teach Poses tab:** Use sliders to teach named poses (optional)
4. Click "Build & Flash"
5. Plug in USB cable
6. Wait for upload (30 seconds)
7. Unplug USB, robot is ready

**Time:** Programming time + 30s for flash  
**Unchanged from current workflow**

### Daily Control Workflow (Phone)

1. Power on robot (plug in USB power or battery)
2. Wait 5 seconds for ESP32 to boot
3. Open phone WiFi settings
4. Connect to "RobotArm-XXXX" (password: robot1234)
5. Browser opens automatically (captive portal)
6. See control interface with 5 sliders + mode toggle
7. Control servos in Manual mode or toggle to Auto mode to run program

**Time:** ~30 seconds first time, ~10 seconds thereafter  
**Simpler than current Blynk workflow (no cloud service)**

## Testing Strategy

### Unit Tests
- WebSocket message parsing (JSON validation)
- Servo angle bounds checking (0-180)
- State synchronization logic
- Captive portal redirect logic

### Integration Tests
- Phone connects to AP and loads PWA
- Slider movements control physical servos
- Mode toggle switches between manual/auto
- Multiple clients can connect simultaneously
- Auto-reconnect works after WiFi drop
- Captive portal triggers on iOS and Android

### Manual Tests
- Test on different phone models (iPhone, Android)
- Test in noisy WiFi environments (classroom with many APs)
- Test with 2-3 simultaneous connections
- Test "Add to Home Screen" functionality
- Test service worker caching
- Test with laptop connected for USB serial monitoring

## Implementation Plan

**Phase 1: ESP32 Firmware**
1. Configure ESP32 as Access Point
2. Add WebSocket server with AsyncWebSocket
3. Implement JSON message handlers
4. Add captive portal DNS responder
5. Test servo control via WebSocket

**Phase 2: PWA Development**
1. Create mobile-optimized HTML/CSS
2. Implement WebSocket client in JavaScript
3. Add slider UI with touch support
4. Add mode toggle and reset button
5. Create PWA manifest and service worker
6. Test on physical devices

**Phase 3: SPIFFS Integration**
1. Upload PWA files to SPIFFS
2. Configure ESPAsyncWebServer to serve from SPIFFS
3. Test complete workflow: connect → load PWA → control

**Phase 4: Desktop IDE Updates**
1. Simplify Setup tab (remove Blynk fields)
2. Remove Blynk Setup tab
3. Update firmware template (remove Blynk, add AP/WebSocket)
4. Update build system to include SPIFFS upload
5. Test end-to-end: build → flash → control

**Phase 5: Documentation**
1. Update setup instructions
2. Create troubleshooting guide
3. Update hardware test checklist
4. Create student quick-start guide

## Security Considerations

**Access Point Password:**
- Default is simple (robot1234) for ease of use
- Configurable in firmware for classrooms needing more security
- WPA2 encryption prevents casual eavesdropping

**WebSocket Communication:**
- Unencrypted (WS not WSS) - acceptable for local network
- No authentication - any connected device can control
- Trade-off: Simplicity vs. security (classroom environment = low threat)

**Captive Portal:**
- Only serves PWA, no other web access
- Prevents accidental internet browsing on robot network

**Future Enhancement:**
- Add optional password authentication in PWA
- Log commands for audit trail
- Rate limiting for malicious spam prevention

## Benefits Over Current System

| Aspect | Current (Blynk) | New (AP + PWA) |
|--------|----------------|----------------|
| Setup complexity | High (WiFi + Blynk account) | Low (just flash firmware) |
| Internet required | Yes | No |
| Cloud service dependency | Yes | No |
| Cost | Free tier (limits apply) | Free (no cloud) |
| Connection reliability | Depends on WiFi/Internet | Direct connection, very reliable |
| Latency | 200-500ms (cloud roundtrip) | 50ms (local) |
| Multi-user control | Limited by Blynk plan | Unlimited concurrent clients |
| Classroom deployment | Complex (WiFi for each robot) | Simple (each robot is its own AP) |
| Offline capable | No | Yes |
| App store approval | N/A (uses Blynk app) | N/A (PWA works immediately) |

## Limitations & Trade-offs

**Limitations:**
- No remote control over internet (must be in WiFi range)
- ESP32 AP range ~50 meters (typical classroom is fine)
- Can't control robot from home (by design)
- Max 4-8 simultaneous clients (ESP32 AP limitation)

**Trade-offs accepted:**
- WebSocket adds complexity vs. REST API → Better UX worth it
- PWA vs. Native app → Faster deployment, works on all platforms
- USB flash only → Simpler workflow, one less thing to break
- No authentication → Easier for students, acceptable risk in classroom

**Out of scope:**
- Internet connectivity (explicitly removed)
- OTA (Over-The-Air) firmware updates (USB is fine)
- Native mobile app development (PWA is sufficient)
- Multi-robot orchestration (single robot control only)

## Success Criteria

**Functional:**
- Student can connect phone to robot WiFi within 30 seconds
- PWA loads and displays control interface
- All 5 servo sliders control corresponding servos in real-time
- Mode toggle switches between manual and auto correctly
- Multiple students can control same robot simultaneously
- Captive portal works on iOS and Android

**Non-functional:**
- Latency under 100ms for slider → servo movement
- Works in classroom with 10+ robots nearby
- Setup takes under 5 minutes (first time)
- Daily use takes under 30 seconds (connect → control)
- Battery life unaffected (WiFi AP uses similar power to WiFi client)

**Documentation:**
- Student quick-start guide (1 page)
- Troubleshooting guide for common issues
- Updated IDE setup instructions
- Hardware test checklist updated

## Open Questions

None - all design questions answered during brainstorming.

## Appendix: Technology Choices

**ESP32 Libraries:**
- `ESPAsyncWebServer` - Efficient async HTTP server
- `AsyncWebSocket` - WebSocket support for real-time communication
- `DNSServer` - Captive portal DNS redirection
- `SPIFFS` - File system for serving PWA files
- `ArduinoJson` - JSON parsing (already in use)

**Frontend Technologies:**
- Vanilla JavaScript (no framework overhead)
- CSS Grid/Flexbox for responsive layout
- Web Components API for modular UI (optional)
- Service Workers API for PWA features

**Development Tools:**
- arduino-cli for compilation (unchanged)
- esptool for USB flashing (unchanged)
- SPIFFS upload tool for PWA files
- Chrome DevTools for PWA debugging
