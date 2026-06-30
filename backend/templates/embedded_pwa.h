// Embedded PWA HTML (all-in-one, no SPIFFS needed)
const char EMBEDDED_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Robot Arm</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #0a0a0a; color: #fff; padding: 20px; }
        .container { max-width: 500px; margin: 0 auto; }
        h1 { font-size: 24px; margin-bottom: 20px; text-align: center; }
        .status { text-align: center; padding: 10px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; }
        .connected { background: #10b981; }
        .connecting { background: #f59e0b; }
        .disconnected { background: #ef4444; }
        .servo { background: #1a1a1a; padding: 15px; margin-bottom: 15px; border-radius: 8px; }
        .servo label { display: block; margin-bottom: 8px; font-weight: 600; }
        .slider-row { display: flex; align-items: center; gap: 10px; }
        .slider-row span:first-child { min-width: 30px; font-size: 12px; color: #888; }
        .slider-row span:last-child { min-width: 50px; font-size: 14px; text-align: right; font-weight: 600; }
        input[type="range"] { flex: 1; height: 6px; border-radius: 3px; background: #333; outline: none; -webkit-appearance: none; }
        input[type="range"]::-webkit-slider-thumb { -webkit-appearance: none; width: 20px; height: 20px; border-radius: 50%; background: #3b82f6; cursor: pointer; }
        input[type="range"]::-moz-range-thumb { width: 20px; height: 20px; border-radius: 50%; background: #3b82f6; cursor: pointer; border: none; }
        input[type="range"]:disabled { opacity: 0.5; cursor: not-allowed; }
        .buttons { display: flex; gap: 10px; margin-top: 20px; }
        button { flex: 1; padding: 15px; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.1s; }
        button:active { transform: scale(0.95); }
        .btn-manual { background: #3b82f6; color: #fff; }
        .btn-auto { background: #10b981; color: #fff; }
        .btn-reset { background: #ef4444; color: #fff; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Robot Arm Control</h1>
        <div id="status" class="status connecting">Connecting...</div>

        <div class="servo">
            <label>Base</label>
            <div class="slider-row">
                <span>0°</span>
                <input type="range" id="s0" min="0" max="180" value="0" disabled>
                <span id="v0">0°</span>
            </div>
        </div>

        <div class="servo">
            <label>Shoulder</label>
            <div class="slider-row">
                <span>0°</span>
                <input type="range" id="s1" min="0" max="180" value="60" disabled>
                <span id="v1">60°</span>
            </div>
        </div>

        <div class="servo">
            <label>Elbow</label>
            <div class="slider-row">
                <span>0°</span>
                <input type="range" id="s2" min="0" max="180" value="70" disabled>
                <span id="v2">70°</span>
            </div>
        </div>

        <div class="servo">
            <label>Wrist</label>
            <div class="slider-row">
                <span>0°</span>
                <input type="range" id="s3" min="0" max="180" value="60" disabled>
                <span id="v3">60°</span>
            </div>
        </div>

        <div class="servo">
            <label>Gripper</label>
            <div class="slider-row">
                <span>0°</span>
                <input type="range" id="s4" min="0" max="180" value="90" disabled>
                <span id="v4">90°</span>
            </div>
        </div>

        <div class="buttons">
            <button id="manual" class="btn-manual">Manual</button>
            <button id="auto" class="btn-auto">Auto</button>
            <button id="reset" class="btn-reset">Reset</button>
        </div>
    </div>

    <script>
        let ws;
        const status = document.getElementById('status');
        const sliders = [0,1,2,3,4].map(i => document.getElementById('s'+i));
        const values = [0,1,2,3,4].map(i => document.getElementById('v'+i));

        function connect() {
            ws = new WebSocket('ws://192.168.4.1/ws');
            ws.onopen = () => {
                status.textContent = 'Connected';
                status.className = 'status connected';
                sliders.forEach(s => s.disabled = false);
            };
            ws.onclose = () => {
                status.textContent = 'Disconnected';
                status.className = 'status disconnected';
                sliders.forEach(s => s.disabled = true);
                setTimeout(connect, 2000);
            };
            ws.onmessage = (e) => {
                const msg = JSON.parse(e.data);
                if(msg.type === 'state') {
                    msg.servos.forEach((angle, i) => {
                        sliders[i].value = angle;
                        values[i].textContent = angle + '°';
                    });
                }
            };
        }

        sliders.forEach((slider, i) => {
            slider.oninput = () => {
                const angle = parseInt(slider.value);
                values[i].textContent = angle + '°';
                if(ws && ws.readyState === 1) {
                    ws.send(JSON.stringify({type:'servo', channel:i, angle:angle}));
                }
            };
        });

        document.getElementById('manual').onclick = () => {
            if(ws && ws.readyState === 1) ws.send(JSON.stringify({type:'mode', auto:false}));
        };

        document.getElementById('auto').onclick = () => {
            if(ws && ws.readyState === 1) ws.send(JSON.stringify({type:'mode', auto:true}));
        };

        document.getElementById('reset').onclick = () => {
            if(ws && ws.readyState === 1) ws.send(JSON.stringify({type:'reset'}));
        };

        connect();
    </script>
</body>
</html>
)rawliteral";
