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

export async function fetchPrograms(projectName = 'default') {
    const response = await fetch(`${API_BASE}/programs?project_name=${projectName}`);
    const data = await response.json();
    if (data.status === 'success') {
        return data.programs;
    }
    throw new Error('Failed to load programs');
}

export async function saveProgram(name, workspace, projectName = 'default') {
    const response = await fetch(`${API_BASE}/programs?project_name=${projectName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, workspace })
    });
    const data = await response.json();
    if (data.status !== 'success') {
        throw new Error(data.message || 'Failed to save program');
    }
    return data.programs;
}

export async function deleteProgram(name, projectName = 'default') {
    const response = await fetch(`${API_BASE}/programs/${name}?project_name=${projectName}`, {
        method: 'DELETE'
    });
    const data = await response.json();
    if (data.status !== 'success') {
        throw new Error(data.message || 'Failed to delete program');
    }
    return data.programs;
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

// ── ESP32-CAM proxy (Vision tab) ────────────────────────────────────────────

export async function pingCamera(baseUrl) {
    const response = await fetch(`${API_BASE}/camera/ping?url=${encodeURIComponent(baseUrl)}`);
    if (!response.ok) throw new Error('Ping request failed');
    return await response.json();   // { reachable: bool, url: string }
}

export async function fetchCameraFrame(baseUrl, rotate = 0) {
    const captureUrl = baseUrl.replace(/\/$/, '') + '/capture';
    const response = await fetch(
        `${API_BASE}/camera/frame?url=${encodeURIComponent(captureUrl)}&rotate=${rotate}`
    );
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Could not fetch frame from ESP32-CAM');
    }
    return await response.blob();   // JPEG blob, same as webcam canvas.toBlob()
}

export async function fetchDetectStatus() {
    const response = await fetch(`${API_BASE}/detect/status`);
    const data = await response.json();
    return data.model_available === true;
}

export async function detectImage(blob, conf = 0.5) {
    const formData = new FormData();
    formData.append('image', blob, 'frame.jpg');
    const response = await fetch(`${API_BASE}/detect?conf=${conf}`, {
        method: 'POST',
        body: formData
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Detection failed');
    }
    return await response.json();
}

// ── Drop-zone masks (Vision tab exclusion ROI) ──────────────────────────────

export async function fetchDropZones(projectName = 'default') {
    const response = await fetch(`${API_BASE}/detect/drop-zones?project_name=${projectName}`);
    if (!response.ok) throw new Error('Failed to load drop zones');
    const data = await response.json();
    return data.drop_zones;   // { enabled, zones: [{left,top,right,bottom}, ...] }
}

export async function saveDropZones(dropZones, projectName = 'default') {
    const response = await fetch(`${API_BASE}/detect/drop-zones?project_name=${projectName}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dropZones)
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to save drop zones');
    }
    const data = await response.json();
    return data.drop_zones;
}

// ── Custom-dataset training (Train Model tab) ───────────────────────────────

export async function uploadDataset(file, projectName = 'default') {
    const formData = new FormData();
    formData.append('dataset', file, file.name || 'dataset.zip');
    formData.append('project_name', projectName);
    const response = await fetch(`${API_BASE}/train/upload`, { method: 'POST', body: formData });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
    }
    return data;  // { classes, num_classes, num_images, data_yaml }
}

export async function startTraining(projectName = 'default', epochs = 20, imgsz = 640) {
    const formData = new FormData();
    formData.append('project_name', projectName);
    formData.append('epochs', epochs);
    formData.append('imgsz', imgsz);
    const response = await fetch(`${API_BASE}/train/start`, { method: 'POST', body: formData });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || 'Could not start training');
    }
    return data;
}

export async function fetchTrainStatus() {
    const response = await fetch(`${API_BASE}/train/status`);
    return await response.json();  // { state, epoch, total_epochs, message, classes }
}

export async function fetchModelClasses(projectName = 'default') {
    const response = await fetch(`${API_BASE}/train/classes?project_name=${projectName}`);
    const data = await response.json();
    return data.classes || [];
}

export async function fetchSerialPorts() {
    const response = await fetch(`${API_BASE}/ports`);
    const data = await response.json();
    if (data.status !== 'success') {
        throw new Error('Failed to list serial ports');
    }
    return data.ports;
}

export async function uploadFirmware({ port, generatedCode = '', projectName = 'default' }) {
    const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            port,
            generated_code: generatedCode,
            target_board: 'arm',
            project_name: projectName,
        }),
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
    }
    return data;
}

export async function buildManualMode(projectName = 'default') {
    const response = await fetch(`${API_BASE}/build/manual?project_name=${projectName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Build failed');
    }

    return await response.json();
}
