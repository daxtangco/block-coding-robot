// Build panel for compiling and downloading firmware
import { buildFirmware, buildManualMode } from '../api.js';

export function initBuildPanel() {
    const buildBtn = document.getElementById('build-btn');
    const modal = document.getElementById('build-modal');
    const closeBtn = modal?.querySelector('.modal-close');

    buildBtn.addEventListener('click', async () => {
        // Check which workspace is active
        const activeTab = document.querySelector('.workspace-tabs .tab.active');
        const activeWorkspace = activeTab?.dataset.workspace;

        // If on Setup or Blynk Setup tab, build for manual mode
        if (activeWorkspace === 'setup' || activeWorkspace === 'blynk-setup') {
            await buildForManualMode(modal);
            return;
        }

        // Otherwise, build with program blocks
        await buildWithBlocks(modal);
    });

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.classList.remove('active');
        });
    }

    // Close modal on background click
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    }
}

async function buildForManualMode(modal) {
    // Show modal
    showModal(modal);
    showBuildProgress('Building firmware for manual control...');

    try {
        const result = await buildManualMode();
        showBuildSuccess(result);
    } catch (error) {
        showBuildError(error.message || 'Build failed');
    }
}

async function buildWithBlocks(modal) {
    // Check if we have a workspace with blocks
    if (!window.blocklyWorkspace) {
        alert('Please switch to the Program workspace first!');
        return;
    }

    // Generate code from Blockly
    const code = window.generateArduinoCode ? window.generateArduinoCode() : '';

    if (!code || code.trim() === '') {
        alert('No code to compile! Add some blocks to your program first.');
        return;
    }

    // Show modal
    showModal(modal);
    showBuildProgress('Compiling your program...');

    try {
        const result = await buildFirmware(code);
        showBuildSuccess(result);
    } catch (error) {
        showBuildError(error.message || 'Build failed');
    }
}

function showModal(modal) {
    if (modal) {
        modal.style.display = 'block';
        modal.classList.add('active');
    }
}

function showBuildProgress(message) {
    const progress = document.getElementById('build-progress');
    const status = document.getElementById('build-status');
    const buildResult = document.getElementById('build-result');

    if (progress) progress.style.display = 'block';
    if (status) status.textContent = message;
    if (buildResult) buildResult.style.display = 'none';
}

function showBuildSuccess(result) {
    const progress = document.getElementById('build-progress');
    const buildResult = document.getElementById('build-result');

    if (progress) progress.style.display = 'none';
    if (buildResult) {
        buildResult.style.display = 'block';

        // Calculate firmware size
        const sizeKB = result.firmware_size ? (result.firmware_size / 1024).toFixed(1) : 'Unknown';

        // Store firmware URL for flash buttons
        window.lastBuildUrl = result.download_url;

        buildResult.innerHTML = `
            <div class="result-success">
                <h3>✅ Build Successful!</h3>
                <p><strong>Firmware size:</strong> ${sizeKB} KB</p>
                <p><strong>Target:</strong> ESP32 Arm Controller (PCA9685)</p>

                <div class="flash-options">
                    <h4>Choose flashing method:</h4>

                    <button id="flash-usb-btn" class="btn-primary flash-option">
                        <span class="btn-icon">🔌</span>
                        <div>
                            <strong>Flash via USB</strong>
                            <small>Use Web Serial API (Chrome/Edge)</small>
                        </div>
                    </button>

                    <button id="download-bin-btn" class="btn-secondary flash-option">
                        <span class="btn-icon">💾</span>
                        <div>
                            <strong>Download .bin File</strong>
                            <small>For manual flashing</small>
                        </div>
                    </button>

                    <p class="warning-text" id="browser-warning" style="display: none;">
                        ⚠️ USB flashing requires Chrome or Edge browser
                    </p>
                </div>
            </div>
        `;

        // Re-attach flash handlers
        attachFlashHandlers(result.download_url);
    }
}

function attachFlashHandlers(firmwareUrl) {
    const flashUsbBtn = document.getElementById('flash-usb-btn');
    const downloadBinBtn = document.getElementById('download-bin-btn');
    const browserWarning = document.getElementById('browser-warning');

    if (flashUsbBtn) {
        flashUsbBtn.addEventListener('click', async () => {
            // Check browser support
            if (!new ESP32Flasher().isSupported()) {
                if (browserWarning) browserWarning.style.display = 'block';
                return;
            }

            // Hide build modal
            const buildModal = document.getElementById('build-modal');
            if (buildModal) buildModal.style.display = 'none';

            // Start flash
            const flashUI = new FlashUI();
            await flashUI.startFlash(firmwareUrl);
        });
    }

    if (downloadBinBtn) {
        downloadBinBtn.addEventListener('click', () => {
            const link = document.createElement('a');
            link.href = firmwareUrl;
            link.download = 'robot_firmware.bin';
            link.click();
        });
    }
}

function showBuildError(errorMessage) {
    const progress = document.getElementById('build-progress');
    const buildResult = document.getElementById('build-result');

    if (progress) progress.style.display = 'none';
    if (buildResult) {
        buildResult.style.display = 'block';
        buildResult.innerHTML = `
            <div style="padding: 1rem; background: #fee2e2; border-radius: 0.5rem; border: 1px solid #fca5a5;">
                <h3 style="color: var(--danger-color); margin-bottom: 0.5rem;">❌ Build Failed</h3>
                <pre style="color: #991b1b; font-size: 0.85rem; white-space: pre-wrap; max-height: 300px; overflow: auto;">${errorMessage}</pre>
                <p style="margin-top: 1rem; color: var(--text-secondary); font-size: 0.9rem;">
                    Common issues:
                    <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                        <li>arduino-cli not installed (see docs/ARDUINO_CLI_SETUP.md)</li>
                        <li>WiFi/Blynk settings not configured (go to Setup tab)</li>
                        <li>ESP32 board not installed: <code>arduino-cli core install esp32:esp32</code></li>
                        <li>Missing library: <code>arduino-cli lib install "Adafruit PWM Servo Driver Library"</code></li>
                    </ul>
                </p>
            </div>
        `;
    }
}
