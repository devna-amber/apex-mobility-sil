// plant-models/safety-fsm-verilog/bms_interlock.v
// Deterministic Hardware Safety Interlock FSM for EV High-Voltage Contactor Control

module bms_interlock (
    input  wire       clk,              // System clock (e.g., 10 MHz)
    input  wire       rst_n,            // Active-low synchronous reset
    input  wire       ign_on,           // Ignition / Drive enable request
    input  wire       over_temp_fault,  // Triggered when cell temp > 60 C
    input  wire       over_curr_fault,  // Triggered when discharge > 350 A
    input  wire       crc_err_fault,    // Triggered by x86-64 ASM checksum mismatch
    output reg        contactor_closed, // 1 = HV Bus Active, 0 = HV Bus Isolated
    output reg        derate_active,    // 1 = Limit motor torque to 50%
    output reg  [1:0] current_state     // Exposed state for SIL telemetry logging
);

    // State Encoding
    localparam STATE_IDLE          = 2'b00;
    localparam STATE_NOMINAL       = 2'b01;
    localparam STATE_DERATE        = 2'b10;
    localparam STATE_FAULT_LOCKOUT = 2'b11;

    reg [1:0] next_state;

    // Sequential State Transition
    always @(posedge clk) begin
        if (!rst_n) begin
            current_state <= STATE_IDLE;
        end else begin
            current_state <= next_state;
        end
    end

    // Combinational Next-State Logic (Single-Cycle Fault Trip)
    always @(*) begin
        next_state = current_state;
        case (current_state)
            STATE_IDLE: begin
                if (over_temp_fault || over_curr_fault || crc_err_fault)
                    next_state = STATE_FAULT_LOCKOUT;
                else if (ign_on)
                    next_state = STATE_NOMINAL;
            end

            STATE_NOMINAL: begin
                if (over_temp_fault || over_curr_fault)
                    next_state = STATE_FAULT_LOCKOUT;
                else if (crc_err_fault)
                    next_state = STATE_DERATE;
                else if (!ign_on)
                    next_state = STATE_IDLE;
            end

            STATE_DERATE: begin
                if (over_temp_fault || over_curr_fault)
                    next_state = STATE_FAULT_LOCKOUT;
                else if (!crc_err_fault && ign_on)
                    next_state = STATE_NOMINAL;
                else if (!ign_on)
                    next_state = STATE_IDLE;
            end

            STATE_FAULT_LOCKOUT: begin
                // Latched lockout: requires explicit hardware reset (rst_n = 0)
                next_state = STATE_FAULT_LOCKOUT;
            end

            default: next_state = STATE_FAULT_LOCKOUT;
        endcase
    end

    // Output Logic
    always @(*) begin
        case (current_state)
            STATE_IDLE: begin
                contactor_closed = 1'b0;
                derate_active    = 1'b0;
            end
            STATE_NOMINAL: begin
                contactor_closed = 1'b1;
                derate_active    = 1'b0;
            end
            STATE_DERATE: begin
                contactor_closed = 1'b1;
                derate_active    = 1'b1;
            end
            STATE_FAULT_LOCKOUT: begin
                contactor_closed = 1'b0;
                derate_active    = 1'b0;
            end
            default: begin
                contactor_closed = 1'b0;
                derate_active    = 1'b0;
            end
        endcase
    end

endmodule
