// Pose teaching interface
import { fetchPoses, savePose, deletePose } from '../api.js';

let currentPoses = {};

export async function initPoseTeaching() {
    // Initialize servo control sliders
    const sliders = ['base', 'shoulder', 'elbow', 'wrist', 'gripper'];
    sliders.forEach(servo => {
        const slider = document.getElementById(`pose-${servo}`);
        const display = slider.nextElementSibling;

        slider.addEventListener('input', (e) => {
            display.textContent = `${e.target.value}°`;
        });
    });

    // Save pose button
    document.getElementById('save-pose-btn').addEventListener('click', async () => {
        const name = prompt('Enter a name for this pose:');
        if (!name) return;

        // Validate name
        if (!/^[A-Z_][A-Z0-9_]*$/i.test(name)) {
            alert('Pose name must start with a letter and contain only letters, numbers, and underscores.');
            return;
        }

        const angles = [
            parseInt(document.getElementById('pose-base').value),
            parseInt(document.getElementById('pose-shoulder').value),
            parseInt(document.getElementById('pose-elbow').value),
            parseInt(document.getElementById('pose-wrist').value),
            parseInt(document.getElementById('pose-gripper').value)
        ];

        try {
            currentPoses = await savePose(name, angles);
            await renderPosesList();
            updatePoseCount();
            alert(`✅ Pose "${name}" saved successfully!`);
        } catch (error) {
            alert('❌ Error saving pose: ' + error.message);
        }
    });

    // Load and render existing poses
    await loadPoses();
}

async function loadPoses() {
    try {
        currentPoses = await fetchPoses();
        await renderPosesList();
        updatePoseCount();
    } catch (error) {
        console.error('Failed to load poses:', error);
    }
}

async function renderPosesList() {
    const list = document.getElementById('poses-list');
    list.innerHTML = '';

    if (Object.keys(currentPoses).length === 0) {
        list.innerHTML = '<p style="color: #64748b;">No poses saved yet. Create one using the sliders above!</p>';
        return;
    }

    for (const [name, angles] of Object.entries(currentPoses)) {
        const card = document.createElement('div');
        card.className = 'pose-card';
        card.innerHTML = `
            <div class="pose-card-header">
                <span class="pose-card-name">${name}</span>
                ${name !== 'HOME' ? `<button class="pose-card-delete" data-pose="${name}">🗑️</button>` : ''}
            </div>
            <div class="pose-card-angles">
                [${angles.join(', ')}]
            </div>
        `;

        // Delete button handler
        const deleteBtn = card.querySelector('.pose-card-delete');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', async () => {
                if (!confirm(`Delete pose "${name}"?`)) return;

                try {
                    currentPoses = await deletePose(name);
                    await renderPosesList();
                    updatePoseCount();
                } catch (error) {
                    alert('❌ Error deleting pose: ' + error.message);
                }
            });
        }

        list.appendChild(card);
    }
}

function updatePoseCount() {
    const count = Object.keys(currentPoses).length;
    document.getElementById('pose-count').textContent = `${count} pose${count !== 1 ? 's' : ''}`;
}

// Export current poses for use by Blockly
export function getPoses() {
    return currentPoses;
}
