// Arm control blocks

Blockly.Blocks['move_to_pose'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("move arm to pose")
            .appendField(new Blockly.FieldDropdown(function() {
                // Read live pose list so blocks dragged from toolbox
                // always reflect what's currently saved.
                if (typeof window.getPoseOptions === 'function') {
                    const opts = window.getPoseOptions();
                    if (opts.length > 0) return opts;
                }
                return [['HOME', 'HOME']];
            }), "POSE");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour('#5C81A6');
        this.setTooltip("Move the robot arm to a saved pose");
    }
};

Blockly.Blocks['open_claw'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("open claw");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour('#5C81A6');
        this.setTooltip("Open the gripper claw");
    }
};

Blockly.Blocks['close_claw'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("close claw")
            .appendField(new Blockly.FieldDropdown([
                ["(auto)", "AUTO"],
                ["narrow", "NARROW"],
                ["wide", "WIDE"],
            ]), "GRIP");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour('#5C81A6');
        this.setTooltip("Close the gripper. (auto) picks narrow/wide from the piece " +
            "the camera sees; narrow (8°) grips thin 1-stud pieces, wide (13°) " +
            "stops short so a thick 2-stud piece doesn't stall the servo.");
    }
};

Blockly.Blocks['wait_for_arm'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("wait for arm to finish");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour('#5C81A6');
        this.setTooltip("Wait for servos to reach position");
    }
};
