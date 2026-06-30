// Vision blocks

// Built-in LEGO classes from the pretrained YOLO model, plus any objects the
// student taught in the Teach Object tab (published on window.__taughtClasses
// after training). Generated fresh each time the dropdown opens.
const BUILTIN_CAMERA_CLASSES = [
    ["brick 1x6", "brick_1x6"],
    ["brick 2x2", "brick_2x2"],
    ["brick 2x4", "brick_2x4"],
    ["plate 1x2", "plate_1x2"],
    ["plate 2x2", "plate_2x2"],
    ["plate 2x4", "plate_2x4"],
];

function cameraClassOptions() {
    const taught = (window.__taughtClasses || []).map(name => [`${name} (taught)`, name]);
    return [...BUILTIN_CAMERA_CLASSES, ...taught, ["nothing", "none"]];
}

Blockly.Blocks['camera_sees'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("camera sees")
            .appendField(new Blockly.FieldDropdown(cameraClassOptions), "CLASS")
            .appendField("with confidence >")
            .appendField(new Blockly.FieldNumber(70, 0, 100), "CONFIDENCE")
            .appendField("%");
        this.setOutput(true, "Boolean");
        this.setColour('#745BA5');
        this.setTooltip("Check if camera detects a specific object class");
    }
};

Blockly.Blocks['current_detection'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("current detection");
        this.setOutput(true, "String");
        this.setColour('#745BA5');
        this.setTooltip("Get the currently detected object class name");
    }
};

Blockly.Blocks['current_confidence'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("current confidence %");
        this.setOutput(true, "Number");
        this.setColour('#745BA5');
        this.setTooltip("Get the confidence level of current detection (0-100)");
    }
};
