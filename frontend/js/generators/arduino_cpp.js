// Arduino C++ code generator for Blockly

// Initialize Arduino generator
Blockly.Arduino = new Blockly.Generator('Arduino');

// Blockly v10+ looks up per-block generators in `generator.forBlock[type]`
// rather than directly on the generator object. Alias forBlock to the
// generator itself so the `Blockly.Arduino['type'] = fn` assignments below
// register where blockToCode expects them.
Blockly.Arduino.forBlock = Blockly.Arduino;

// Reserved words
Blockly.Arduino.addReservedWords(
    'setup,loop,if,else,for,switch,case,while,do,break,continue,return,goto,' +
    'const,int,float,double,char,void,bool,String'
);

// Order of operations
Blockly.Arduino.ORDER_ATOMIC = 0;
Blockly.Arduino.ORDER_UNARY_POSTFIX = 1;
Blockly.Arduino.ORDER_UNARY_PREFIX = 2;
Blockly.Arduino.ORDER_MULTIPLICATIVE = 3;
Blockly.Arduino.ORDER_ADDITIVE = 4;
Blockly.Arduino.ORDER_RELATIONAL = 5;
Blockly.Arduino.ORDER_EQUALITY = 6;
Blockly.Arduino.ORDER_LOGICAL_AND = 7;
Blockly.Arduino.ORDER_LOGICAL_OR = 8;
Blockly.Arduino.ORDER_NONE = 99;

// Workspace to code
Blockly.Arduino.workspaceToCode = function(workspace) {
    this.init(workspace);

    // Get all top-level blocks
    const blocks = workspace.getTopBlocks(true);
    let code = '';

    // Generate code for each top-level block
    for (let i = 0; i < blocks.length; i++) {
        const blockCode = this.blockToCode(blocks[i]);
        if (blockCode) {
            code += blockCode;
        }
    }

    return code;
};

Blockly.Arduino.init = function(workspace) {
    // Reset everything
    this.definitions_ = Object.create(null);
    // v10+ renamed variableDB_ -> nameDB_. Keep both pointing at one Names
    // instance so variable blocks resolve regardless of which the version uses.
    this.nameDB_ = new Blockly.Names(this.RESERVED_WORDS_);
    this.variableDB_ = this.nameDB_;
};

Blockly.Arduino.finish = function(code) {
    return code;
};

Blockly.Arduino.scrubNakedValue = function(line) {
    return line + ';\n';
};

Blockly.Arduino.scrub_ = function(block, code, opt_thisOnly) {
    if (code === null) return '';
    let commentCode = '';
    if (!opt_thisOnly) {
        if (block && block.nextConnection && block.nextConnection.targetBlock()) {
            commentCode += this.blockToCode(block.nextConnection.targetBlock());
        }
    }
    return code + commentCode;
};

// ===== ARM BLOCKS =====

Blockly.Arduino['move_to_pose'] = function(block) {
    const pose = block.getFieldValue('POSE');
    // Uppercase to match the C++ const name the backend generates
    // (template_engine.py builds POSE_<NAME.upper()>). Without this, a pose
    // whose name has lowercase letters (e.g. "PICKUP2x2") produces an
    // undeclared-identifier compile error.
    return `moveArmToPose(POSE_${pose.toUpperCase()});\n`;
};

Blockly.Arduino['open_claw'] = function(block) {
    return 'openClaw();\n';
};

Blockly.Arduino['close_claw'] = function(block) {
    return 'closeClaw();\n';
};

Blockly.Arduino['wait_for_arm'] = function(block) {
    return 'delay(200);\n';
};

// ===== VISION BLOCKS =====

Blockly.Arduino['camera_sees'] = function(block) {
    const className = block.getFieldValue('CLASS');
    const confidence = block.getFieldValue('CONFIDENCE');
    const code = `cameraSees("${className}", ${confidence})`;
    return [code, Blockly.Arduino.ORDER_ATOMIC];
};

Blockly.Arduino['current_detection'] = function(block) {
    return ['lastDetection', Blockly.Arduino.ORDER_ATOMIC];
};

Blockly.Arduino['current_confidence'] = function(block) {
    return ['lastConfidence', Blockly.Arduino.ORDER_ATOMIC];
};

// ===== LOGIC BLOCKS =====

Blockly.Arduino['forever_loop'] = function(block) {
    const branch = Blockly.Arduino.statementToCode(block, 'DO');
    // Loop while in auto mode (not `while(true)`) so pressing Manual breaks out —
    // autoMode is volatile and set by the WebSocket Manual button. AP mode uses
    // WebSocket/AsyncWebServer, so no Blynk.run() needed.
    return `while (autoMode) {\n${branch}}\n`;
};

Blockly.Arduino['wait_seconds'] = function(block) {
    const seconds = block.getFieldValue('SECONDS');
    const milliseconds = parseFloat(seconds) * 1000;
    return `delay(${milliseconds});\n`;
};

// ===== STANDARD BLOCKLY BLOCKS =====

Blockly.Arduino['controls_if'] = function(block) {
    let code = '';
    let n = 0;
    if (block.getInput('IF' + n)) {
        let condition = Blockly.Arduino.valueToCode(block, 'IF' + n, Blockly.Arduino.ORDER_NONE) || 'false';
        let branch = Blockly.Arduino.statementToCode(block, 'DO' + n);
        code += `if (${condition}) {\n${branch}}`;
        n++;

        while (block.getInput('IF' + n)) {
            condition = Blockly.Arduino.valueToCode(block, 'IF' + n, Blockly.Arduino.ORDER_NONE) || 'false';
            branch = Blockly.Arduino.statementToCode(block, 'DO' + n);
            code += ` else if (${condition}) {\n${branch}}`;
            n++;
        }

        if (block.getInput('ELSE')) {
            branch = Blockly.Arduino.statementToCode(block, 'ELSE');
            code += ` else {\n${branch}}`;
        }
    }
    return code + '\n';
};

Blockly.Arduino['controls_repeat_ext'] = function(block) {
    const times = Blockly.Arduino.valueToCode(block, 'TIMES', Blockly.Arduino.ORDER_NONE) || '0';
    const branch = Blockly.Arduino.statementToCode(block, 'DO');
    return `for (int i = 0; i < ${times}; i++) {\n${branch}}\n`;
};

Blockly.Arduino['logic_compare'] = function(block) {
    const operators = {
        'EQ': '==',
        'NEQ': '!=',
        'LT': '<',
        'LTE': '<=',
        'GT': '>',
        'GTE': '>='
    };
    const operator = operators[block.getFieldValue('OP')];
    const order = Blockly.Arduino.ORDER_RELATIONAL;
    const arg0 = Blockly.Arduino.valueToCode(block, 'A', order) || '0';
    const arg1 = Blockly.Arduino.valueToCode(block, 'B', order) || '0';
    const code = `${arg0} ${operator} ${arg1}`;
    return [code, order];
};

Blockly.Arduino['math_number'] = function(block) {
    const code = parseFloat(block.getFieldValue('NUM'));
    return [code, Blockly.Arduino.ORDER_ATOMIC];
};

Blockly.Arduino['math_arithmetic'] = function(block) {
    const operators = {
        'ADD': ['+', Blockly.Arduino.ORDER_ADDITIVE],
        'MINUS': ['-', Blockly.Arduino.ORDER_ADDITIVE],
        'MULTIPLY': ['*', Blockly.Arduino.ORDER_MULTIPLICATIVE],
        'DIVIDE': ['/', Blockly.Arduino.ORDER_MULTIPLICATIVE]
    };
    const tuple = operators[block.getFieldValue('OP')];
    const operator = tuple[0];
    const order = tuple[1];
    const arg0 = Blockly.Arduino.valueToCode(block, 'A', order) || '0';
    const arg1 = Blockly.Arduino.valueToCode(block, 'B', order) || '0';
    const code = `${arg0} ${operator} ${arg1}`;
    return [code, order];
};

Blockly.Arduino['variables_get'] = function(block) {
    const varName = Blockly.Arduino.nameDB_.getName(block.getFieldValue('VAR'), Blockly.Names.NameType.VARIABLE);
    return [varName, Blockly.Arduino.ORDER_ATOMIC];
};

Blockly.Arduino['variables_set'] = function(block) {
    const varName = Blockly.Arduino.nameDB_.getName(block.getFieldValue('VAR'), Blockly.Names.NameType.VARIABLE);
    const value = Blockly.Arduino.valueToCode(block, 'VALUE', Blockly.Arduino.ORDER_NONE) || '0';
    return `int ${varName} = ${value};\n`;
};

console.log('✅ Arduino code generator loaded');
