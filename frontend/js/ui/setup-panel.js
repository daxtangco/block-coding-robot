// Setup panel for Access Point configuration
import { fetchSettings, saveSettings } from '../api.js';

export async function initSetupPanel() {
    const form = document.getElementById('settings-form');
    const statusDiv = document.getElementById('settings-status');

    // Load existing settings
    await loadSettingsIntoForm();

    // Save settings
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const settings = {
            ap_ssid_suffix: formData.get('ap_ssid_suffix') || '',
            ap_password: formData.get('ap_password') || 'robot1234'
        };

        try {
            await saveSettings(settings);
            showStatus('Settings saved successfully!', 'success');
        } catch (error) {
            showStatus('Error: ' + error.message, 'error');
        }
    });

    async function loadSettingsIntoForm() {
        try {
            const settings = await fetchSettings();

            // Only set values if elements exist (AP mode fields)
            const apSsidInput = document.getElementById('ap_ssid_suffix');
            const apPasswordInput = document.getElementById('ap_password');

            if (apSsidInput) {
                apSsidInput.value = settings.ap_ssid_suffix || '';
            }
            if (apPasswordInput) {
                apPasswordInput.value = settings.ap_password || 'robot1234';
            }
        } catch (error) {
            console.warn('Could not load settings:', error);
            // Initialize with defaults if loading fails
            const apPasswordInput = document.getElementById('ap_password');
            if (apPasswordInput && !apPasswordInput.value) {
                apPasswordInput.value = 'robot1234';
            }
        }
    }

    function showStatus(message, type) {
        statusDiv.textContent = message;
        statusDiv.className = `status-message ${type}`;
        setTimeout(() => {
            statusDiv.className = 'status-message';
        }, 5000);
    }
}
