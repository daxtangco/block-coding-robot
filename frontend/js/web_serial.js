// Web Serial API Flash System
class ESP32Flasher {
    constructor() {
        this.port = null;
        this.reader = null;
        this.writer = null;
        this.connected = false;
    }

    // Check if Web Serial API is supported
    isSupported() {
        return 'serial' in navigator;
    }

    // Request serial port from user
    async requestPort() {
        if (!this.isSupported()) {
            throw new Error('Web Serial API not supported. Use Chrome or Edge browser.');
        }

        try {
            this.port = await navigator.serial.requestPort();
            return true;
        } catch (err) {
            if (err.name === 'NotFoundError') {
                throw new Error('No serial port selected');
            }
            throw err;
        }
    }

    // Connect to serial port
    async connect(baudRate = 115200) {
        if (!this.port) {
            throw new Error('No port selected. Call requestPort() first.');
        }

        try {
            await this.port.open({ baudRate });
            this.reader = this.port.readable.getReader();
            this.writer = this.port.writable.getWriter();
            this.connected = true;
            return true;
        } catch (err) {
            throw new Error(`Failed to connect: ${err.message}`);
        }
    }

    // Disconnect from serial port
    async disconnect() {
        if (this.reader) {
            await this.reader.cancel();
            await this.reader.releaseLock();
            this.reader = null;
        }

        if (this.writer) {
            await this.writer.releaseLock();
            this.writer = null;
        }

        if (this.port) {
            await this.port.close();
            this.port = null;
        }

        this.connected = false;
    }

    // Send command to ESP32
    async sendCommand(data) {
        if (!this.writer) {
            throw new Error('Not connected');
        }

        const encoder = new TextEncoder();
        await this.writer.write(encoder.encode(data));
    }

    // Read response from ESP32
    async readResponse(timeout = 5000) {
        if (!this.reader) {
            throw new Error('Not connected');
        }

        const decoder = new TextDecoder();
        const startTime = Date.now();
        let response = '';

        while (Date.now() - startTime < timeout) {
            const { value, done } = await this.reader.read();
            if (done) break;
            response += decoder.decode(value);
            if (response.includes('\n')) break;
        }

        return response.trim();
    }

    // Flash firmware (stub - implementation in next task)
    async flashFirmware(firmwareData, progressCallback) {
        throw new Error('Flash implementation coming in next task');
    }
}

// Export for use in other modules
window.ESP32Flasher = ESP32Flasher;
