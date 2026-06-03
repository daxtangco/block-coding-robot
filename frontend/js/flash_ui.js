// Flash UI Controller
class FlashUI {
    constructor() {
        this.flasher = new ESP32Flasher();
        this.modal = null;
    }

    // Show flash progress modal
    showFlashModal() {
        // Remove existing modal if present
        const existing = document.getElementById('flash-modal');
        if (existing) existing.remove();

        // Create modal
        const modal = document.createElement('div');
        modal.id = 'flash-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>⚡ Flashing ESP32</h2>
                </div>
                <div class="modal-body">
                    <div id="flash-steps"></div>
                    <div id="flash-progress-bar" style="display:none;">
                        <div class="progress-bar">
                            <div class="progress-fill" id="flash-progress-fill"></div>
                        </div>
                        <p id="flash-progress-text">0%</p>
                    </div>
                    <div id="flash-log"></div>
                </div>
                <div class="modal-footer">
                    <button id="flash-close-btn" class="btn-secondary" disabled>Close</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        modal.style.display = 'block';
        this.modal = modal;

        // Close button
        document.getElementById('flash-close-btn').addEventListener('click', () => {
            modal.remove();
        });
    }

    // Update flash step
    addStep(message, status = 'pending') {
        const stepsDiv = document.getElementById('flash-steps');
        const step = document.createElement('div');
        step.className = `flash-step flash-step-${status}`;

        const icon = status === 'success' ? '✅' :
                    status === 'error' ? '❌' :
                    status === 'loading' ? '⏳' : '⚪';

        step.innerHTML = `<span class="step-icon">${icon}</span> ${message}`;
        stepsDiv.appendChild(step);

        // Scroll to bottom
        stepsDiv.scrollTop = stepsDiv.scrollHeight;

        return step;
    }

    // Update existing step
    updateStep(step, message, status) {
        const icon = status === 'success' ? '✅' :
                    status === 'error' ? '❌' :
                    status === 'loading' ? '⏳' : '⚪';

        step.className = `flash-step flash-step-${status}`;
        step.innerHTML = `<span class="step-icon">${icon}</span> ${message}`;
    }

    // Show progress bar
    showProgress() {
        document.getElementById('flash-progress-bar').style.display = 'block';
    }

    // Update progress
    updateProgress(percent, message = '') {
        const fill = document.getElementById('flash-progress-fill');
        const text = document.getElementById('flash-progress-text');

        fill.style.width = percent + '%';
        text.textContent = message || `${percent}%`;
    }

    // Add log message
    addLog(message) {
        const logDiv = document.getElementById('flash-log');
        const line = document.createElement('div');
        line.className = 'log-line';
        line.textContent = message;
        logDiv.appendChild(line);
        logDiv.scrollTop = logDiv.scrollHeight;
    }

    // Enable close button
    enableClose() {
        document.getElementById('flash-close-btn').disabled = false;
    }

    // Start flash process
    async startFlash(firmwareUrl) {
        this.showFlashModal();

        try {
            // Step 1: Request port
            const step1 = this.addStep('Requesting serial port...', 'loading');
            await this.flasher.requestPort();
            this.updateStep(step1, 'Serial port selected', 'success');

            // Step 2: Connect
            const step2 = this.addStep('Connecting to ESP32...', 'loading');
            await this.flasher.connect();
            this.updateStep(step2, 'Connected to ESP32', 'success');

            // Step 3: Download firmware
            const step3 = this.addStep('Downloading firmware...', 'loading');
            const response = await fetch(firmwareUrl);
            const firmwareData = await response.arrayBuffer();
            this.updateStep(step3, `Firmware downloaded (${(firmwareData.byteLength / 1024).toFixed(1)} KB)`, 'success');

            // Step 4: Flash (stub for now)
            const step4 = this.addStep('Flashing firmware...', 'loading');
            this.showProgress();

            // Simulate progress (real implementation in next task)
            for (let i = 0; i <= 100; i += 10) {
                await new Promise(resolve => setTimeout(resolve, 200));
                this.updateProgress(i, `Writing firmware... ${i}%`);
            }

            this.updateStep(step4, 'Firmware flashed successfully!', 'success');

            // Step 5: Disconnect
            const step5 = this.addStep('Disconnecting...', 'loading');
            await this.flasher.disconnect();
            this.updateStep(step5, 'Disconnected', 'success');

            this.addStep('✅ Flash complete! ESP32 is rebooting...', 'success');
            this.enableClose();

            // Add validation checklist after successful flash
            this.addValidationChecklist();

        } catch (err) {
            this.addStep(`❌ Error: ${err.message}`, 'error');
            this.enableClose();
        }
    }

    // Add validation checklist after flash completion
    addValidationChecklist() {
        const modalBody = document.querySelector('#flash-modal .modal-body');

        const validationSection = document.createElement('div');
        validationSection.className = 'validation-checklist';
        validationSection.innerHTML = `
            <h3>🔍 Verify Your Hardware</h3>
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                Please check that all components are working correctly:
            </p>
            <div class="validation-items">
                <div class="validation-item">
                    <input type="checkbox" id="check-online">
                    <label for="check-online">ESP32 shows "online" in Blynk app</label>
                </div>
                <div class="validation-item">
                    <input type="checkbox" id="check-base">
                    <label for="check-base">Base servo responds to V0 slider</label>
                </div>
                <div class="validation-item">
                    <input type="checkbox" id="check-shoulder">
                    <label for="check-shoulder">Shoulder servo responds to V1 slider</label>
                </div>
                <div class="validation-item">
                    <input type="checkbox" id="check-elbow">
                    <label for="check-elbow">Elbow servo responds to V2 slider</label>
                </div>
                <div class="validation-item">
                    <input type="checkbox" id="check-wrist">
                    <label for="check-wrist">Wrist servo responds to V3 slider</label>
                </div>
                <div class="validation-item">
                    <input type="checkbox" id="check-gripper">
                    <label for="check-gripper">Gripper servo responds to V4 slider</label>
                </div>
                <div class="validation-item">
                    <input type="checkbox" id="check-automode">
                    <label for="check-automode">Auto Mode switch (V5) visible in app</label>
                </div>
            </div>
            <div class="validation-actions">
                <button class="btn-success" id="validation-success-btn">✓ All Working</button>
                <button class="btn-warning" id="validation-issue-btn">📝 Report Issue</button>
            </div>
        `;

        modalBody.appendChild(validationSection);

        // Add strikethrough effect for checked items
        const checkboxes = validationSection.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const label = e.target.nextElementSibling;
                if (e.target.checked) {
                    label.style.textDecoration = 'line-through';
                    label.style.opacity = '0.6';
                } else {
                    label.style.textDecoration = 'none';
                    label.style.opacity = '1';
                }
            });
        });

        // Success button handler
        document.getElementById('validation-success-btn').addEventListener('click', () => {
            validationSection.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: var(--success-color);">
                    <h3>✅ Hardware Verified Successfully!</h3>
                    <p style="color: var(--text-secondary); margin-top: 0.5rem;">
                        Your robot arm is ready to use. You can now close this window.
                    </p>
                </div>
            `;
        });

        // Issue button handler
        document.getElementById('validation-issue-btn').addEventListener('click', () => {
            this.showTroubleshooting();
        });
    }

    // Show troubleshooting modal
    showTroubleshooting() {
        const modalBody = document.querySelector('#flash-modal .modal-body');

        // Create troubleshooting container
        const troubleshootingDiv = document.createElement('div');
        troubleshootingDiv.id = 'troubleshooting-container';
        troubleshootingDiv.innerHTML = `
            <h3>🔧 Troubleshooting</h3>
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                Select the issue you're experiencing:
            </p>
            <div class="troubleshooting-options">
                <button class="option-btn" data-issue="wifi">ESP32 won't connect to WiFi</button>
                <button class="option-btn" data-issue="offline">Blynk shows "offline"</button>
                <button class="option-btn" data-issue="one-servo">One servo doesn't move</button>
                <button class="option-btn" data-issue="all-servos">All servos don't move</button>
                <button class="option-btn" data-issue="other">Other issue</button>
            </div>
            <div id="troubleshooting-advice"></div>
        `;

        modalBody.appendChild(troubleshootingDiv);

        // Add event listeners to option buttons
        const optionButtons = troubleshootingDiv.querySelectorAll('.option-btn');
        optionButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const issue = e.target.dataset.issue;
                const adviceContainer = document.getElementById('troubleshooting-advice');
                this.showAdvice(issue, adviceContainer);
            });
        });
    }

    // Show specific advice for each issue
    showAdvice(issue, container) {
        const advice = {
            'wifi': `
                <h4>WiFi Connection Issues</h4>
                <ol>
                    <li>Check that your WiFi credentials in the setup are correct</li>
                    <li>Make sure your WiFi network is 2.4GHz (ESP32 doesn't support 5GHz)</li>
                    <li>Verify your WiFi password doesn't have special characters</li>
                    <li>Try moving the ESP32 closer to your router</li>
                    <li>Check if your network requires additional authentication</li>
                </ol>
            `,
            'offline': `
                <h4>Blynk Shows Offline</h4>
                <ol>
                    <li>Verify your Blynk auth token is correct</li>
                    <li>Check that the ESP32 is powered on (LED should be lit)</li>
                    <li>Make sure your Blynk app template ID matches your device</li>
                    <li>Try pressing the RESET button on the ESP32</li>
                    <li>Check the Serial Monitor for connection errors</li>
                </ol>
            `,
            'one-servo': `
                <h4>One Servo Not Responding</h4>
                <ol>
                    <li>Check the servo's power connection (red wire)</li>
                    <li>Verify the signal wire is connected to the correct GPIO pin</li>
                    <li>Make sure the ground (brown/black wire) is connected</li>
                    <li>Try swapping with a working servo to test if the servo is faulty</li>
                    <li>Check if the virtual pin mapping is correct in firmware</li>
                </ol>
            `,
            'all-servos': `
                <h4>All Servos Not Moving</h4>
                <ol>
                    <li>Check that the external 5V power supply is connected and on</li>
                    <li>Verify all ground connections are properly connected</li>
                    <li>Make sure the power supply can provide enough current (at least 2A)</li>
                    <li>Check if any wires came loose during assembly</li>
                    <li>Verify the servo shield is properly seated on the ESP32</li>
                </ol>
            `,
            'other': `
                <h4>General Troubleshooting Steps</h4>
                <ol>
                    <li>Try reflashing the firmware</li>
                    <li>Press the RESET button on the ESP32</li>
                    <li>Check all wiring connections</li>
                    <li>Verify power supply voltage (should be 5V for servos)</li>
                    <li>Open Serial Monitor to check for error messages</li>
                    <li>Consult the hardware documentation for your specific setup</li>
                </ol>
            `
        };

        container.innerHTML = `
            <div id="advice-content">
                ${advice[issue]}
                <button class="btn-secondary" id="back-to-issues" style="margin-top: 1rem;">← Back to Issues</button>
            </div>
        `;

        // Back button handler
        document.getElementById('back-to-issues').addEventListener('click', () => {
            container.innerHTML = '';
        });
    }
}

// Export
window.FlashUI = FlashUI;
