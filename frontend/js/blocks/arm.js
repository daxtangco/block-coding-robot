// Arm control blocks

Blockly.Blocks['move_to_pose'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("move arm to pose")
            .appendField(new Blockly.FieldDropdown([["HOME", "HOME"]]), "POSE");
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
            .appendField("close claw");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour('#5C81A6');
        this.setTooltip("Close the gripper claw");
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
