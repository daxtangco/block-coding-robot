// Logic and flow control blocks

Blockly.Blocks['forever_loop'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("forever");
        this.appendStatementInput("DO")
            .appendField("do");
        this.setColour('#5CA65C');
        this.setTooltip("Repeat the enclosed blocks forever");
        this.setHelpUrl("");
    }
};

Blockly.Blocks['wait_seconds'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("wait")
            .appendField(new Blockly.FieldNumber(1, 0), "SECONDS")
            .appendField("seconds");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour('#5CA65C');
        this.setTooltip("Pause program execution for specified seconds");
    }
};
