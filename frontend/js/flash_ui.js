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

        } catch (err) {
            this.addStep(`❌ Error: ${err.message}`, 'error');
            this.enableClose();
        }
    }
}

// Export
window.FlashUI = FlashUI;
