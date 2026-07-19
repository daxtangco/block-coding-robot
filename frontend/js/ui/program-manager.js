// Save/load/delete named block programs. Persists the Blockly workspace
// serialization (the blocks, not the generated C++) to the backend so a
// program can be reopened and edited later instead of rebuilt from scratch.
import { fetchPrograms, saveProgram, deleteProgram } from '../api.js';

let currentPrograms = {};

const NAME_RE = /^[A-Z_][A-Z0-9_]*$/i;

export async function initProgramManager() {
    document.getElementById('save-program-btn')?.addEventListener('click', onSave);
    document.getElementById('load-program-btn')?.addEventListener('click', onLoad);
    document.getElementById('delete-program-btn')?.addEventListener('click', onDelete);

    await refreshPrograms();
}

async function refreshPrograms() {
    try {
        currentPrograms = await fetchPrograms();
    } catch (e) {
        console.error('Failed to load programs:', e);
        currentPrograms = {};
    }
    renderProgramSelect();
}

function renderProgramSelect() {
    const select = document.getElementById('program-select');
    if (!select) return;
    const names = Object.keys(currentPrograms);
    if (names.length === 0) {
        select.innerHTML = '<option value="">No saved programs</option>';
        return;
    }
    select.innerHTML = names
        .map(n => `<option value="${n}">${n}</option>`)
        .join('');
}

async function onSave() {
    const workspace = window.blocklyWorkspace;
    if (!workspace) {
        alert('Blockly workspace not ready.');
        return;
    }
    if (workspace.getAllBlocks().length === 0) {
        alert('Nothing to save — add some blocks first.');
        return;
    }

    const name = prompt('Enter a name for this program:');
    if (!name) return;
    if (!NAME_RE.test(name)) {
        alert('Program name must start with a letter and contain only letters, numbers, and underscores.');
        return;
    }
    if (currentPrograms[name] && !confirm(`A program named "${name}" already exists. Overwrite it?`)) {
        return;
    }

    const serialized = Blockly.serialization.workspaces.save(workspace);
    try {
        currentPrograms = await saveProgram(name, serialized);
        renderProgramSelect();
        document.getElementById('program-select').value = name;
        alert(`Program "${name}" saved.`);
    } catch (e) {
        alert('Error saving program: ' + e.message);
    }
}

function onLoad() {
    const workspace = window.blocklyWorkspace;
    if (!workspace) {
        alert('Blockly workspace not ready.');
        return;
    }
    const name = document.getElementById('program-select')?.value;
    if (!name || !currentPrograms[name]) {
        alert('Select a saved program to load.');
        return;
    }
    if (workspace.getAllBlocks().length > 0 &&
        !confirm('Loading will replace the current blocks. Continue?')) {
        return;
    }

    try {
        workspace.clear();
        Blockly.serialization.workspaces.load(currentPrograms[name], workspace);
    } catch (e) {
        console.error('Failed to load program:', e);
        alert('Could not load program "' + name + '". It may be corrupt.');
    }
}

async function onDelete() {
    const name = document.getElementById('program-select')?.value;
    if (!name || !currentPrograms[name]) {
        alert('Select a saved program to delete.');
        return;
    }
    if (!confirm(`Delete program "${name}"?`)) return;

    try {
        currentPrograms = await deleteProgram(name);
        renderProgramSelect();
    } catch (e) {
        alert('Error deleting program: ' + e.message);
    }
}
