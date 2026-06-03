// Blynk Setup Guide
class BlynkSetupGuide {
    constructor() {
        this.standardSetupBtn = document.getElementById('standard-setup-btn');
        this.customSetupBtn = document.getElementById('custom-setup-btn');
        this.guideContainer = document.getElementById('blynk-guide-container');

        this.initEventListeners();
    }

    initEventListeners() {
        this.standardSetupBtn?.addEventListener('click', () => {
            this.showStandardSetup();
        });

        this.customSetupBtn?.addEventListener('click', () => {
            this.showCustomSetup();
        });
    }

    showStandardSetup() {
        this.guideContainer.style.display = 'block';
        this.guideContainer.innerHTML = `
            <div class="blynk-guide">
                <div class="guide-layout">
                    <div class="preview-panel">
                        <h3>📱 App Preview</h3>
                        <div class="blynk-mockup">
                            <div class="mockup-header">Robot Controller</div>
                            <div class="mockup-widget">
                                <span class="widget-label">Base</span>
                                <input type="range" min="0" max="180" value="90" disabled>
                                <span class="widget-value">0 ← → 180</span>
                            </div>
                            <div class="mockup-widget">
                                <span class="widget-label">Shoulder</span>
                                <input type="range" min="0" max="180" value="90" disabled>
                                <span class="widget-value">0 ← → 180</span>
                            </div>
                            <div class="mockup-widget">
                                <span class="widget-label">Elbow</span>
                                <input type="range" min="0" max="180" value="90" disabled>
                                <span class="widget-value">0 ← → 180</span>
                            </div>
                            <div class="mockup-widget">
                                <span class="widget-label">Wrist</span>
                                <input type="range" min="0" max="180" value="90" disabled>
                                <span class="widget-value">0 ← → 180</span>
                            </div>
                            <div class="mockup-widget">
                                <span class="widget-label">Gripper</span>
                                <input type="range" min="0" max="180" value="30" disabled>
                                <span class="widget-value">0 ← → 180</span>
                            </div>
                            <div class="mockup-widget">
                                <span class="widget-label">Auto Mode</span>
                                <label class="switch">
                                    <input type="checkbox" disabled>
                                    <span class="slider"></span>
                                </label>
                            </div>
                        </div>
                    </div>

                    <div class="steps-panel">
                        <h3>📝 Setup Steps</h3>
                        <p class="instructions">Follow these steps in your Blynk mobile app:</p>

                        <div class="checklist">
                            ${this.generateWidgetSteps()}
                        </div>

                        <div class="quick-copy">
                            <h4>📋 Quick Copy</h4>
                            ${this.generateQuickCopy()}
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Attach copy handlers after DOM update
        setTimeout(() => this.attachCopyHandlers(), 0);
    }

    generateWidgetSteps() {
        const widgets = [
            { pin: 'V0', label: 'Base', type: 'Slider', range: '0-180' },
            { pin: 'V1', label: 'Shoulder', type: 'Slider', range: '0-180' },
            { pin: 'V2', label: 'Elbow', type: 'Slider', range: '0-180' },
            { pin: 'V3', label: 'Wrist', type: 'Slider', range: '0-180' },
            { pin: 'V4', label: 'Gripper', type: 'Slider', range: '0-180' },
            { pin: 'V5', label: 'Auto Mode', type: 'Switch', range: '0/1' }
        ];

        return widgets.map((w, i) => `
            <div class="checklist-item">
                <input type="checkbox" id="widget-${i}">
                <label for="widget-${i}">
                    <strong>${w.type}:</strong> ${w.pin} - "${w.label}" (${w.range})
                </label>
            </div>
        `).join('');
    }

    generateQuickCopy() {
        const widgets = [
            { pin: 'V0', label: 'Base (0-180)' },
            { pin: 'V1', label: 'Shoulder (0-180)' },
            { pin: 'V2', label: 'Elbow (0-180)' },
            { pin: 'V3', label: 'Wrist (0-180)' },
            { pin: 'V4', label: 'Gripper (0-180)' },
            { pin: 'V5', label: 'Auto Mode (0/1)' }
        ];

        return widgets.map(w => `
            <div class="copy-item">
                <code>${w.pin}: ${w.label}</code>
                <button class="btn-copy" data-copy="${w.pin}: ${w.label}">Copy</button>
            </div>
        `).join('');
    }

    attachCopyHandlers() {
        document.querySelectorAll('.btn-copy').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const textToCopy = e.target.dataset.copy;
                try {
                    await navigator.clipboard.writeText(textToCopy);
                    e.target.textContent = '✓ Copied';
                    e.target.classList.add('copied');
                    setTimeout(() => {
                        e.target.textContent = 'Copy';
                        e.target.classList.remove('copied');
                    }, 2000);
                } catch (err) {
                    console.error('Copy failed:', err);
                    e.target.textContent = '✗ Failed';
                    setTimeout(() => {
                        e.target.textContent = 'Copy';
                    }, 2000);
                }
            });
        });
    }

    showCustomSetup() {
        this.guideContainer.style.display = 'block';
        this.guideContainer.innerHTML = `
            <div class="custom-setup-notice">
                <p>🔧 Custom setup allows you to configure different widgets.</p>
                <p><em>Coming in Phase 2 - For now, please use Standard Setup.</em></p>
                <button class="btn-secondary" id="back-to-standard">← Back to Standard Setup</button>
            </div>
        `;

        document.getElementById('back-to-standard')?.addEventListener('click', () => {
            this.showStandardSetup();
        });
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new BlynkSetupGuide();
    });
} else {
    new BlynkSetupGuide();
}
