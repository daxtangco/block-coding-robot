// Shared store for the most recent webcam detection result.
//
// vision-panel.js writes here on every detection loop; the program-runner reads
// it when evaluating camera_sees / current_detection / current_confidence. This
// decouples the two so the runner never has to know how detection is produced.

let latest = null;       // last /api/detect result, or null if none yet
let latestAt = 0;        // millis timestamp of that result

export function setLatestDetection(result) {
    latest = result;
    latestAt = Date.now();
}

export function clearLatestDetection() {
    latest = null;
    latestAt = 0;
}

// The raw result ({detections, count, bin_statistics, ...}) or null.
export function getLatestDetection() {
    return latest;
}

// Age in ms of the latest result, or Infinity if there is none. The runner can
// use this to treat stale data (camera stopped) as "no detection".
export function detectionAge() {
    return latest ? Date.now() - latestAt : Infinity;
}
