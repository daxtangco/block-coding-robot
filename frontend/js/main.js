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

        console.log('✅ IDE ready!');
    } catch (error) {
        console.error('❌ Initialization error:', error);
        alert('Failed to initialize IDE: ' + error.message);
    }
});

// Make Blockly workspace available globally for debugging
window.getBlocklyWorkspace = () => window.blocklyWorkspace;
