// Blockly initialization and workspace setup
import { getPoses } from '../ui/pose-teaching.js';
import './arm.js';
import './vision.js';
import './logic.js';
import '../generators/arduino_cpp.js';

export async function initBlockly() {
    const blocklyDiv = document.getElementById('blocklyDiv');

    // Create toolbox
    const toolbox = {
        'kind': 'categoryToolbox',
        'contents': [
            {
                'kind': 'category',
                'name': 'Arm Control',
                'colour': '#5C81A6',
                'contents': [
                    { 'kind': 'block', 'type': 'move_to_pose' },
                    { 'kind': 'block', 'type': 'open_claw' },
                    { 'kind': 'block', 'type': 'close_claw' },
                    { 'kind': 'block', 'type': 'wait_for_arm' }
                ]
            },
            {
                'kind': 'category',
                'name': 'Vision',
                'colour': '#745BA5',
                'contents': [
                    { 'kind': 'block', 'type': 'camera_sees' },
                    { 'kind': 'block', 'type': 'current_detection' },
                    { 'kind': 'block', 'type': 'current_confidence' }
                ]
            },
            {
                'kind': 'category',
                'name': 'Logic',
                'colour': '#5CA65C',
                'contents': [
                    { 'kind': 'block', 'type': 'controls_if' },
                    { 'kind': 'block', 'type': 'controls_repeat_ext' },
                    { 'kind': 'block', 'type': 'forever_loop' },
                    { 'kind': 'block', 'type': 'wait_seconds' }
                ]
            },
            {
                'kind': 'category',
                'name': 'Math',
                'colour': '#5C68A6',
                'contents': [
                    { 'kind': 'block', 'type': 'math_number' },
                    { 'kind': 'block', 'type': 'math_arithmetic' },
                    { 'kind': 'block', 'type': 'logic_compare' }
                ]
            },
            {
                'kind': 'category',
                'name': 'Variables',
                'colour': '#A55B80',
                'custom': 'VARIABLE'
            }
        ]
    };

    // Initialize workspace
    const workspace = Blockly.inject(blocklyDiv, {
        toolbox: toolbox,
        grid: {
            spacing: 20,
            length: 3,
            colour: '#ccc',
            snap: true
        },
        zoom: {
            controls: true,
            wheel: true,
            startScale: 1.0,
            maxScale: 3,
            minScale: 0.3,
            scaleSpeed: 1.2
        },
        trashcan: true
    });

    // Store workspace globally
    window.blocklyWorkspace = workspace;

    // Update code preview on changes
    workspace.addChangeListener(() => {
        updateCodePreview();
        updateBlockCount();
    });

    // Generate code function
    window.generateArduinoCode = () => {
        return Blockly.Arduino.workspaceToCode(workspace);
    };

    console.log('✅ Blockly initialized');
}

function updateCodePreview() {
    if (!window.blocklyWorkspace) return;

    const code = Blockly.Arduino.workspaceToCode(window.blocklyWorkspace);
    document.getElementById('code-output').textContent = code || '// Add blocks to see generated code';
}

function updateBlockCount() {
    if (!window.blocklyWorkspace) return;

    const blocks = window.blocklyWorkspace.getAllBlocks();
    const count = blocks.length;
    document.getElementById('block-count').textContent = `${count} block${count !== 1 ? 's' : ''}`;
}

// Update pose dropdown options dynamically
export function updatePoseDropdowns() {
    const poses = getPoses();
    const poseOptions = Object.keys(poses).map(name => [name, name]);

    // Update all move_to_pose blocks
    if (window.blocklyWorkspace) {
        const blocks = window.blocklyWorkspace.getAllBlocks();
        blocks.forEach(block => {
            if (block.type === 'move_to_pose') {
                const field = block.getField('POSE');
                if (field) {
                    field.menuGenerator_ = poseOptions;
                }
            }
        });
    }
}
