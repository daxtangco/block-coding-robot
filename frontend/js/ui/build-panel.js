// Build panel for compiling and downloading firmware
import { buildFirmware, buildManualMode, fetchSerialPorts, uploadFirmware } from '../api.js';

// Remember what was last built so the USB-flash button recompiles + uploads
// the SAME thing (manual = empty code, program = the generated blocks).
let lastBuild = { generatedCode: '', isManual: true };

export function initBuildPanel() {
    const buildBtn = document.getElementById('build-btn');
    const modal = document.getElementById('build-modal');
    const closeBtn = modal?.querySelector('.modal-close');

    buildBtn.addEventListener('click', async () => {
        // Check which workspace is active
        const activeTab = document.querySelector('.workspace-tabs .tab.active');
        const activeWorkspace = activeTab?.dataset.workspace;

        // If on Setup tab, build for manual mode (AP mode)
        if (activeWorkspace === 'setup') {
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
        lastBuild = { generatedCode: '', isManual: true };
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
    let code = '';
    try {
        code = window.generateArduinoCode ? window.generateArduinoCode() : '';
    } catch (error) {
        console.error('Error generating code:', error);
        alert('Error generating code from blocks. Please check the console for details.');
        return;
    }

    if (!code || code.trim() === '') {
        alert('No code to compile! Add some blocks to your program first.');
        return;
    }

    // Show modal
    showModal(modal);
    showBuildProgress('Compiling your program...');

    try {
        lastBuild = { generatedCode: code, isManual: false };
        const result = await buildFirmware(code);
        showBuildSuccess(result);
    } catch (error) {
        showBuildError(error.message || 'Build failed');
    }
}

function showModal(modal) {
    if (modal) {
        // Visibility is driven entirely by the `.active` class (CSS: .modal.active
        // { display: flex }). Setting an inline display here would override the
        // class and leave the modal stuck open when close removes `.active`.
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
                <h3>Build Successful!</h3>
                <p><strong>Firmware size:</strong> ${sizeKB} KB</p>
                <p><strong>Target:</strong> ESP32 Arm Controller (PCA9685)</p>

                <div class="flash-options">
                    <h4>Flash to your ESP32:</h4>

                    <div class="flash-port-row">
                        <label for="flash-port-select">USB Port:</label>
                        <select id="flash-port-select"><option value="">Detecting...</option></select>
                        <button id="flash-port-refresh" class="btn-icon-only" title="Refresh ports">🔄</button>
                    </div>

                    <button id="flash-usb-btn" class="btn-primary flash-option">
                        <span class="btn-icon">🔌</span>
                        <div>
                            <strong>Flash via USB</strong>
                            <small>Compiles &amp; writes directly to the board</small>
                        </div>
                    </button>

                    <button id="download-bin-btn" class="btn-secondary flash-option">
                        <span class="btn-icon">💾</span>
                        <div>
                            <strong>Download .bin File</strong>
                            <small>For manual flashing (esptool / Arduino IDE)</small>
                        </div>
                    </button>

                    <div id="flash-upload-log" class="flash-upload-log"></div>
                </div>
            </div>
        `;

        // Re-attach flash handlers
        attachFlashHandlers(result.download_url);
        refreshPortList();
    }
}

async function refreshPortList() {
    const select = document.getElementById('flash-port-select');
    if (!select) return;
    select.innerHTML = '<option value="">Detecting...</option>';
    try {
        const ports = await fetchSerialPorts();
        if (!ports.length) {
            select.innerHTML = '<option value="">No serial ports found</option>';
            return;
        }
        select.innerHTML = ports
            .filter(p => p.port)
            .map(p => `<option value="${p.port}">${p.port}${p.label && p.label !== p.port ? ' — ' + p.label : ''}</option>`)
            .join('');
    } catch (e) {
        select.innerHTML = `<option value="">Error: ${e.message}</option>`;
    }
}

function setUploadLog(msg, isError) {
    const log = document.getElementById('flash-upload-log');
    if (!log) return;
    log.textContent = msg;
    log.style.color = isError ? 'var(--danger-color, #c00)' : 'var(--text-secondary, #888)';
}

function attachFlashHandlers(firmwareUrl) {
    const flashUsbBtn = document.getElementById('flash-usb-btn');
    const downloadBinBtn = document.getElementById('download-bin-btn');
    const refreshBtn = document.getElementById('flash-port-refresh');

    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshPortList);
    }

    if (flashUsbBtn) {
        flashUsbBtn.addEventListener('click', async () => {
            const select = document.getElementById('flash-port-select');
            const port = select?.value;
            if (!port) {
                setUploadLog('Select a USB port first (click 🔄 if none are listed).', true);
                return;
            }

            flashUsbBtn.disabled = true;
            setUploadLog(`Compiling & flashing to ${port}… this can take 30–60s. Do not unplug.`, false);
            try {
                await uploadFirmware({
                    port,
                    generatedCode: lastBuild.generatedCode,
                });
                setUploadLog(`Flashed to ${port}. The board is rebooting — reconnect your phone to RobotArm-XXXX.`, false);
            } catch (e) {
                setUploadLog(`Flash failed: ${e.message}`, true);
            } finally {
                flashUsbBtn.disabled = false;
            }
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
                <h3 style="color: var(--danger-color); margin-bottom: 0.5rem;">Build Failed</h3>
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
