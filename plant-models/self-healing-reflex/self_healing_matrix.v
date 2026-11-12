// plant-models/self-healing-reflex/self_healing_matrix.v
// Single-Cycle Self-Healing EV Battery String Bypass & Autonomous Limp-Home Controller

module self_healing_matrix (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [2:0] string_fault,      // Bitmask of faulty battery strings [S2, S1, S0]
    input  wire       thermal_runaway,   // Global pack thermal emergency flag
    output reg  [2:0] string_active,     // 1 = String connected to HV bus, 0 = Bypassed
    output reg        main_hv_contactor, // 1 = Pack delivering power, 0 = Total isolation
    output reg  [1:0] av_mobility_mode   // 00=STOP, 01=LIMP_HOME_SHOULDER, 10=NOMINAL
);

    localparam MODE_STOP      = 2'b00;
    localparam MODE_LIMP_HOME = 2'b01;
    localparam MODE_NOMINAL   = 2'b10;

    // Count how many battery strings have failed
    wire [1:0] fault_count;
    assign fault_count = string_fault[0] + string_fault[1] + string_fault[2];

    always @(posedge clk) begin
        if (!rst_n) begin
            string_active     <= 3'b000;
            main_hv_contactor <= 1'b0;
            av_mobility_mode  <= MODE_STOP;
        end else if (thermal_runaway || fault_count >= 2'd2) begin
            // Cascading or thermal fault: mandatory total HV isolation
            string_active     <= 3'b000;
            main_hv_contactor <= 1'b0;
            av_mobility_mode  <= MODE_STOP;
        end else if (fault_count == 2'd1) begin
            // Single-string fault: bypass only the damaged string, keep 2 healthy strings online
            string_active     <= ~string_fault;
            main_hv_contactor <= 1'b1;
            av_mobility_mode  <= MODE_LIMP_HOME;
        end else begin
            // All 3 battery strings healthy
            string_active     <= 3'b111;
            main_hv_contactor <= 1'b1;
            av_mobility_mode  <= MODE_NOMINAL;
        end
    end

endmodule
