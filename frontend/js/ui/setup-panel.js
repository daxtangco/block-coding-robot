// Setup panel for WiFi and Blynk configuration
import { fetchSettings, saveSettings } from '../api.js';

export async function initSetupPanel() {
    const form = document.getElementById('settings-form');
    const loadBtn = document.getElementById('load-settings-btn');
    const statusDiv = document.getElementById('settings-status');

    // Load existing settings
    await loadSettingsIntoForm();

    // Save settings
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const settings = {
            wifi_ssid: formData.get('wifi_ssid'),
            wifi_password: formData.get('wifi_password'),
            blynk_template_id: formData.get('blynk_template_id'),
            blynk_template_name: formData.get('blynk_template_name'),
            blynk_auth_token: formData.get('blynk_auth_token')
        };

        try {
            await saveSettings(settings);
            showStatus('✅ Settings saved successfully!', 'success');
        } catch (error) {
            showStatus('❌ Error: ' + error.message, 'error');
        }
    });

    // Reload settings
    loadBtn.addEventListener('click', async () => {
        try {
            await loadSettingsIntoForm();
            showStatus('✅ Settings reloaded', 'success');
        } catch (error) {
            showStatus('❌ Error: ' + error.message, 'error');
        }
    });

    async function loadSettingsIntoForm() {
        const settings = await fetchSettings();
        document.getElementById('wifi_ssid').value = settings.wifi_ssid || '';
        document.getElementById('wifi_password').value = settings.wifi_password || '';
        document.getElementById('blynk_template_id').value = settings.blynk_template_id || '';
        document.getElementById('blynk_template_name').value = settings.blynk_template_name || '';
        document.getElementById('blynk_auth_token').value = settings.blynk_auth_token || '';
    }

    function showStatus(message, type) {
        statusDiv.textContent = message;
        statusDiv.className = `status-message ${type}`;
        setTimeout(() => {
            statusDiv.className = 'status-message';
        }, 5000);
    }
}
