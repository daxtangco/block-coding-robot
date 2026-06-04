// WebSocket connection
let ws = null;
let reconnectInterval = null;
const WS_URL = 'ws://192.168.4.1/ws';
const RECONNECT_DELAY = 2000;

// UI Elements
const statusIndicator = document.getElementById('connection-status');
const sliders = document.querySelectorAll('input[type="range"]');
const manualBtn = document.getElementById('manual-btn');
const autoBtn = document.getElementById('auto-btn');
const resetBtn = document.getElementById('reset-btn');

// Current state
let isAutoMode = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setupSliders();
    setupModeButtons();
    setupResetButton();
    connect();
});

// Connect to WebSocket
function connect() {
    updateStatus('connecting');

    try {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
            console.log('WebSocket connected');
            updateStatus('connected');
            enableControls();
            clearReconnectTimer();
        };

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                handleMessage(message);
            } catch (error) {
                console.error('Failed to parse message:', error);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            updateStatus('disconnected');
            disableControls();
            scheduleReconnect();
        };
    } catch (error) {
        console.error('Failed to create WebSocket:', error);
        updateStatus('disconnected');
        scheduleReconnect();
    }
}

// Schedule reconnection attempt
function scheduleReconnect() {
    if (reconnectInterval) return;

    reconnectInterval = setInterval(() => {
        console.log('Attempting to reconnect...');
        connect();
    }, RECONNECT_DELAY);
}

// Clear reconnection timer
function clearReconnectTimer() {
    if (reconnectInterval) {
        clearInterval(reconnectInterval);
        reconnectInterval = null;
    }
}

// Update connection status UI
function updateStatus(status) {
    statusIndicator.className = `status-indicator ${status}`;

    const statusText = {
        'connected': 'Connected',
        'disconnected': 'Disconnected',
        'connecting': 'Connecting...'
    };

    statusIndicator.textContent = statusText[status] || status;
}

// Enable all controls
function enableControls() {
    sliders.forEach(slider => slider.disabled = false);
    manualBtn.disabled = false;
    autoBtn.disabled = false;
    resetBtn.disabled = false;
}

// Disable all controls
function disableControls() {
    sliders.forEach(slider => slider.disabled = true);
    manualBtn.disabled = true;
    autoBtn.disabled = true;
    resetBtn.disabled = true;
}

// Handle incoming WebSocket messages
function handleMessage(message) {
    console.log('Received:', message);

    if (message.type === 'state') {
        // Update slider positions from ESP32 state
        if (Array.isArray(message.servos) && message.servos.length === 5) {
            const servoIds = ['base', 'shoulder', 'elbow', 'wrist', 'gripper'];
            message.servos.forEach((angle, index) => {
                const slider = document.getElementById(`servo-${servoIds[index]}`);
                const valueSpan = document.getElementById(`value-${servoIds[index]}`);
                if (slider && valueSpan) {
                    slider.value = angle;
                    valueSpan.textContent = angle + '°';
                }
            });
        }

        // Update mode
        if (typeof message.auto === 'boolean') {
            isAutoMode = message.auto;
            updateModeButtons();
        }
    }
}

// Send message to ESP32
function sendMessage(message) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(message));
        console.log('Sent:', message);
    } else {
        console.warn('WebSocket not connected, message not sent:', message);
    }
}

// Setup slider event listeners
function setupSliders() {
    sliders.forEach(slider => {
        const channel = parseInt(slider.dataset.channel);
        const servoName = slider.id.replace('servo-', '');
        const valueSpan = document.getElementById(`value-${servoName}`);

        // Update value display and send to ESP32
        slider.addEventListener('input', (e) => {
            const angle = parseInt(e.target.value);
            valueSpan.textContent = angle + '°';

            sendMessage({
                type: 'servo',
                channel: channel,
                angle: angle
            });
        });
    });
}

// Setup mode button event listeners
function setupModeButtons() {
    manualBtn.addEventListener('click', () => {
        if (!isAutoMode) return;
        isAutoMode = false;
        updateModeButtons();
        sendMessage({
            type: 'mode',
            auto: false
        });
    });

    autoBtn.addEventListener('click', () => {
        if (isAutoMode) return;
        isAutoMode = true;
        updateModeButtons();
        sendMessage({
            type: 'mode',
            auto: true
        });
    });
}

// Update mode button active states
function updateModeButtons() {
    if (isAutoMode) {
        manualBtn.classList.remove('active');
        autoBtn.classList.add('active');
    } else {
        manualBtn.classList.add('active');
        autoBtn.classList.remove('active');
    }
}

// Setup reset button
function setupResetButton() {
    resetBtn.addEventListener('click', () => {
        sendMessage({
            type: 'reset'
        });
    });
}
