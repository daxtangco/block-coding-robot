// Shared store for the most recent webcam detection result.
//
// vision-panel.js writes here on every detection loop; the program-runner reads
// it when evaluating camera_sees / current_detection / current_confidence. This
// decouples the two so the runner never has to know how detection is produced.

let latest = null;       // last /api/detect result, or null if none yet
let latestAt = 0;        // millis timestamp of that result

// Rolling history of the top class seen on each of the last N frames. Detection
// flickers frame-to-frame (a brick_2x2 may read as plate_2x2 on one frame), and
// the program branches on class -> a single bad frame sends a piece to the wrong
// drop pose. Voting over recent frames returns the class the camera has agreed on,
// not whatever it happened to see this millisecond.
const HISTORY_SIZE = 7;      // frames kept (~0.4s at the 60ms detect loop)
let classHistory = [];       // most-recent-last list of top class names ('none' if empty frame)

export function setLatestDetection(result) {
    latest = result;
    latestAt = Date.now();
    const top = result && result.detections && result.detections[0];
    classHistory.push(top ? top.class_name : 'none');
    if (classHistory.length > HISTORY_SIZE) classHistory.shift();
}

export function clearLatestDetection() {
    latest = null;
    latestAt = 0;
    classHistory = [];
}

// The class the camera has AGREED on over recent frames, or null if there's no
// clear winner yet. `minFraction` is how much of the window must agree (default
// majority). Ignores 'none' frames so a brief dropout doesn't reset the vote,
// but returns null if the window is mostly empty. Use this for drop decisions.
export function getStableClass(minFraction = 0.6) {
    const seen = classHistory.filter((c) => c !== 'none');
    if (seen.length < Math.ceil(HISTORY_SIZE * 0.5)) return null;  // too few real frames
    const counts = {};
    for (const c of seen) counts[c] = (counts[c] || 0) + 1;
    let bestClass = null, bestCount = 0;
    for (const [c, n] of Object.entries(counts)) {
        if (n > bestCount) { bestClass = c; bestCount = n; }
    }
    return bestCount / seen.length >= minFraction ? bestClass : null;
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
