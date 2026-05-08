// Vision blocks

Blockly.Blocks['camera_sees'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("camera sees")
            .appendField(new Blockly.FieldDropdown([
                ["red small", "red_small"],
                ["red large", "red_large"],
                ["blue small", "blue_small"],
                ["blue large", "blue_large"],
                ["nothing", "none"]
            ]), "CLASS")
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
