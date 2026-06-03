// Main application initialization
import { initBlockly } from './blocks/index.js';
import { initSetupPanel } from './ui/setup-panel.js';
import { initPoseTeaching } from './ui/pose-teaching.js';
import { initBuildPanel } from './ui/build-panel.js';

// Workspace switching
function initWorkspaces() {
    document.querySelectorAll('.workspace-tabs .tab').forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs
            document.querySelectorAll('.workspace-tabs .tab').forEach(t =>
                t.classList.remove('active')
            );

            // Add active class to clicked tab
            tab.classList.add('active');

            // Hide all workspaces
            document.querySelectorAll('.workspace').forEach(ws =>
                ws.classList.remove('active')
            );

            // Show selected workspace
            const workspaceId = tab.dataset.workspace + '-workspace';
            const workspace = document.getElementById(workspaceId);
            if (workspace) {
                workspace.classList.add('active');
            }

            // Trigger Blockly resize if switching to program workspace
            if (tab.dataset.workspace === 'program' && window.blocklyWorkspace) {
                Blockly.svgResize(window.blocklyWorkspace);
            }
        });
    });
}

// Initialize all components when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🤖 Block Robot IDE initializing...');

    try {
        initWorkspaces();
        await initBlockly();
        await initSetupPanel();
        await initPoseTeaching();
        initBuildPanel();
        initFlashHandlers();

        console.log('✅ IDE ready!');
    } catch (error) {
        console.error('❌ Initialization error:', error);
        alert('Failed to initialize IDE: ' + error.message);
    }
});

// Initialize flash UI handlers
function initFlashHandlers() {
    // Initialize flash UI
    const flashUI = new FlashUI();

    // Flash USB button
    document.getElementById('flash-usb-btn')?.addEventListener('click', async () => {
        // Get firmware URL from build result
        const firmwareUrl = '/api/build/firmware.bin'; // Adjust based on your API

        // Check browser support
        if (!new ESP32Flasher().isSupported()) {
            document.getElementById('browser-warning').style.display = 'block';
            return;
        }

        // Hide build modal
        document.getElementById('build-modal').style.display = 'none';

        // Start flash
        await flashUI.startFlash(firmwareUrl);
    });

    // Download bin button
    document.getElementById('download-bin-btn')?.addEventListener('click', () => {
        const firmwareUrl = '/api/build/firmware.bin'; // Adjust based on your API
        const link = document.createElement('a');
        link.href = firmwareUrl;
        link.download = 'robot_firmware.bin';
        link.click();
    });
}

// Make Blockly workspace available globally for debugging
window.getBlocklyWorkspace = () => window.blocklyWorkspace;
