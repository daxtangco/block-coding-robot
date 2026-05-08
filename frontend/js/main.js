// Main application initialization
import { initBlockly } from './blocks/index.js';
import { initSetupPanel } from './ui/setup-panel.js';
import { initPoseTeaching } from './ui/pose-teaching.js';
import { initBuildPanel } from './ui/build-panel.js';

// Workspace switching
function initWorkspaces() {
    const tabs = document.querySelectorAll('.tab');
    const workspaces = document.querySelectorAll('.workspace');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetWorkspace = tab.dataset.workspace;

            // Update tabs
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Update workspaces
            workspaces.forEach(w => w.classList.remove('active'));
            document.getElementById(`${targetWorkspace}-workspace`).classList.add('active');

            // Trigger Blockly resize if switching to program workspace
            if (targetWorkspace === 'program' && window.blocklyWorkspace) {
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

        console.log('✅ IDE ready!');
    } catch (error) {
        console.error('❌ Initialization error:', error);
        alert('Failed to initialize IDE: ' + error.message);
    }
});

// Make Blockly workspace available globally for debugging
window.getBlocklyWorkspace = () => window.blocklyWorkspace;
