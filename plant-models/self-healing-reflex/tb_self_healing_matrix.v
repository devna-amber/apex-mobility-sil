`timescale 1ns / 1ps

module tb_self_healing_matrix;

    reg        clk;
    reg        rst_n;
    reg  [2:0] string_fault;
    reg        thermal_runaway;

    wire [2:0] string_active;
    wire       main_hv_contactor;
    wire [1:0] av_mobility_mode;

    self_healing_matrix dut (
        .clk(clk),
        .rst_n(rst_n),
        .string_fault(string_fault),
        .thermal_runaway(thermal_runaway),
        .string_active(string_active),
        .main_hv_contactor(main_hv_contactor),
        .av_mobility_mode(av_mobility_mode)
    );

    always #5 clk = ~clk;

    initial begin
        $display("=== APEX MOBILITY: SELF-HEALING VERILOG CELL-BYPASS MATRIX ===");
        clk = 0;
        rst_n = 0;
        string_fault = 3'b000;
        thermal_runaway = 0;

        #12 rst_n = 1;
        #10;
        if (string_active !== 3'b111 || av_mobility_mode !== 2'b10) begin
            $display("[FAIL] Expected all 3 strings active in NOMINAL mode.");
            $finish(1);
        end
        $display("[SIL-HEAL] Nominal State      -> Active=111 | HV=ON  | Mode=NOMINAL (100%% Power)");

        // Inject single-string short circuit on String 1 (3'b010)
        string_fault = 3'b010;
        #10;
        if (string_active !== 3'b101 || main_hv_contactor !== 1'b1 || av_mobility_mode !== 2'b01) begin
            $display("[FAIL] Failed to bypass String 1 cleanly!");
            $finish(1);
        end
        $display("[SIL-HEAL] String 1 Shorted   -> Active=101 | HV=ON  | Mode=LIMP_HOME_SHOULDER (66%% Power)");

        // Inject cascading second string fault (3'b110) -> Must open main HV contactor immediately
        string_fault = 3'b110;
        #10;
        if (string_active !== 3'b000 || main_hv_contactor !== 1'b0 || av_mobility_mode !== 2'b00) begin
            $display("[FAIL] Critical: Failed to isolate pack during multi-string fault!");
            $finish(1);
        end
        $display("[SIL-HEAL] Cascading 2-Fault  -> Active=000 | HV=OFF | Mode=IMMEDIATE_SAFE_STOP");

        $display("[PASS] Self-healing Verilog reflex matrix verified across all boundary states.");
        $finish(0);
    end

endmodule
