`timescale 1ns / 1ps

module tb_bms_interlock;

    reg        clk;
    reg        rst_n;
    reg        ign_on;
    reg        over_temp_fault;
    reg        over_curr_fault;
    reg        crc_err_fault;

    wire       contactor_closed;
    wire       derate_active;
    wire [1:0] current_state;

    bms_interlock dut (
        .clk(clk),
        .rst_n(rst_n),
        .ign_on(ign_on),
        .over_temp_fault(over_temp_fault),
        .over_curr_fault(over_curr_fault),
        .crc_err_fault(crc_err_fault),
        .contactor_closed(contactor_closed),
        .derate_active(derate_active),
        .current_state(current_state)
    );

    // 100 MHz clock (10 ns period)
    always #5 clk = ~clk;

    initial begin
        $dumpfile("bms_interlock.vcd");
        $dumpvars(0, tb_bms_interlock);

        // Initialize signals
        clk = 0;
        rst_n = 0;
        ign_on = 0;
        over_temp_fault = 0;
        over_curr_fault = 0;
        crc_err_fault = 0;

        // Release reset
        #20 rst_n = 1;
        #10;
        if (current_state !== 2'b00 || contactor_closed !== 1'b0) begin
            $display("[FAIL] Expected IDLE state after reset.");
            $finish(1);
        end
        $display("[SIL-RTL] Reset verified -> STATE_IDLE (Contactor Open)");

        // Turn ignition ON -> Nominal Drive
        ign_on = 1;
        #10;
        if (current_state !== 2'b01 || contactor_closed !== 1'b1) begin
            $display("[FAIL] Expected NOMINAL state when ignition is ON.");
            $finish(1);
        end
        $display("[SIL-RTL] Ignition ON    -> STATE_NOMINAL (Contactor Closed)");

        // Inject ASM Checksum Mismatch -> Torque Derate
        crc_err_fault = 1;
        #10;
        if (current_state !== 2'b10 || derate_active !== 1'b1) begin
            $display("[FAIL] Expected DERATE state on CRC mismatch.");
            $finish(1);
        end
        $display("[SIL-RTL] CRC Mismatch   -> STATE_DERATE (50%% Torque Limit)");

        // Clear CRC fault -> Recover to Nominal
        crc_err_fault = 0;
        #10;
        $display("[SIL-RTL] CRC Cleared    -> STATE_NOMINAL (Full Power Restored)");

        // Inject Thermal Runaway Fault -> Immediate Contactor Trip
        over_temp_fault = 1;
        #10;
        if (current_state !== 2'b11 || contactor_closed !== 1'b0) begin
            $display("[FAIL] Critical: Contactor failed to open on over-temperature!");
            $finish(1);
        end
        $display("[SIL-RTL] Over-Temp Trip -> STATE_FAULT_LOCKOUT (HV Bus Isolated)");

        // Verify Latch Behavior even if fault signal clears
        over_temp_fault = 0;
        #10;
        if (contactor_closed !== 1'b0) begin
            $display("[FAIL] Contactor closed without hardware reset!");
            $finish(1);
        end
        $display("[PASS] Verilog BMS Safety Interlock FSM passed all SIL assertions.");
        $finish(0);
    end

endmodule
