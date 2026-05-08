// API helper functions for backend communication

const API_BASE = '/api';

export async function fetchSettings(projectName = 'default') {
    const response = await fetch(`${API_BASE}/settings?project_name=${projectName}`);
    const data = await response.json();
    if (data.status === 'success') {
        return data.settings;
    }
    throw new Error('Failed to load settings');
}

export async function saveSettings(settings, projectName = 'default') {
    const response = await fetch(`${API_BASE}/settings?project_name=${projectName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
    });
    const data = await response.json();
    if (data.status !== 'success') {
        throw new Error(data.message || 'Failed to save settings');
    }
    return data;
}

export async function fetchPoses(projectName = 'default') {
    const response = await fetch(`${API_BASE}/poses?project_name=${projectName}`);
    const data = await response.json();
    if (data.status === 'success') {
        return data.poses;
    }
    throw new Error('Failed to load poses');
}

export async function savePose(name, angles, projectName = 'default') {
    const response = await fetch(`${API_BASE}/poses?project_name=${projectName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, angles })
    });
    const data = await response.json();
    if (data.status !== 'success') {
        throw new Error(data.message || 'Failed to save pose');
    }
    return data.poses;
}

export async function deletePose(name, projectName = 'default') {
    const response = await fetch(`${API_BASE}/poses/${name}?project_name=${projectName}`, {
        method: 'DELETE'
    });
    const data = await response.json();
    if (data.status !== 'success') {
        throw new Error(data.message || 'Failed to delete pose');
    }
    return data.poses;
}

export async function buildFirmware(generatedCode, targetBoard = 'arm', projectName = 'default') {
    const response = await fetch(`${API_BASE}/build`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            generated_code: generatedCode,
            target_board: targetBoard,
            project_name: projectName
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Build failed');
    }

    return await response.json();
}
