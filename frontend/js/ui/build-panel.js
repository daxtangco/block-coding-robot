// Build panel for compiling and downloading firmware
import { buildFirmware } from '../api.js';

export function initBuildPanel() {
    const buildBtn = document.getElementById('build-btn');
    const modal = document.getElementById('build-modal');
    const closeBtn = modal.querySelector('.modal-close');

    buildBtn.addEventListener('click', async () => {
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
        modal.classList.add('active');
        showBuildProgress('Compiling your program...');

        try {
            const result = await buildFirmware(code);
            showBuildSuccess(result);
        } catch (error) {
            showBuildError(error.message);
        }
    });

    closeBtn.addEventListener('click', () => {
        modal.classList.remove('active');
    });

    // Close modal on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
}

function showBuildProgress(message) {
    document.getElementById('build-progress').style.display = 'block';
    document.getElementById('build-status').textContent = message;
    document.getElementById('build-log').classList.remove('active');
    document.getElementById('build-result').innerHTML = '';
}

function showBuildSuccess(result) {
    document.getElementById('build-progress').style.display = 'none';

    // Show build log
    const logDiv = document.getElementById('build-log');
    logDiv.classList.add('active');
    logDiv.textContent = result.build_log;

    // Show download button
    const resultDiv = document.getElementById('build-result');
    resultDiv.innerHTML = `
        <div style="text-align: center; padding: 1rem;">
            <h3 style="color: var(--success-color); margin-bottom: 1rem;">✅ Build Successful!</h3>
            <a href="${result.download_url}" class="download-link" download>
                ⬇️ Download Firmware (.bin)
            </a>
            <p style="margin-top: 1rem; color: var(--text-secondary); font-size: 0.9rem;">
                Flash this file to your ESP32 using esptool.<br>
                See <a href="/static/docs/FLASH_INSTRUCTIONS.md" style="color: var(--primary-color);">Flash Instructions</a> for details.
            </p>
        </div>
    `;
}

function showBuildError(errorMessage) {
    document.getElementById('build-progress').style.display = 'none';

    const resultDiv = document.getElementById('build-result');
    resultDiv.innerHTML = `
        <div style="padding: 1rem; background: #fee2e2; border-radius: 0.5rem; border: 1px solid #fca5a5;">
            <h3 style="color: var(--danger-color); margin-bottom: 0.5rem;">❌ Build Failed</h3>
            <pre style="color: #991b1b; font-size: 0.85rem; white-space: pre-wrap; max-height: 300px; overflow: auto;">${errorMessage}</pre>
            <p style="margin-top: 1rem; color: var(--text-secondary); font-size: 0.9rem;">
                Common issues:
                <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                    <li>arduino-cli not installed (see docs/ARDUINO_CLI_SETUP.md)</li>
                    <li>WiFi/Blynk settings not configured (go to Setup tab)</li>
                    <li>Invalid block configuration</li>
                </ul>
            </p>
        </div>
    `;
}
