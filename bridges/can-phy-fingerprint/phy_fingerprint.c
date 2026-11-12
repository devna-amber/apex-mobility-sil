#include <stdio.h>
#include <stdint.h>
#include <math.h>

// External x86-64 assembly routine reading CPU hardware cycle counter
extern uint64_t read_hw_tsc(void);

typedef struct {
    double baseline_period_cycles;
    double baseline_temp_c;
    double thermal_coeff_ppm_per_c;
    double max_allowed_residual_ppm;
} EcuClockProfile;

// Evaluates whether an arriving CAN frame matches the genuine ECU's hardware crystal signature
int verify_ecu_physical_fingerprint(
    const EcuClockProfile *profile,
    double measured_interval_cycles,
    double ambient_temp_c,
    double *out_residual_ppm
) {
    // 1. Calculate raw clock skew in parts-per-million (ppm)
    double raw_skew_ppm = ((measured_interval_cycles - profile->baseline_period_cycles)
                           / profile->baseline_period_cycles) * 1e6;

    // 2. Compensate for normal ambient crystal oscillator thermal drift (~0.8 ppm/C)
    double expected_thermal_drift = (ambient_temp_c - profile->baseline_temp_c)
                                    * profile->thermal_coeff_ppm_per_c;

    // 3. Residual skew isolates true hardware oscillator identity from temperature shifts
    double residual_ppm = fabs(raw_skew_ppm - expected_thermal_drift);
    if (out_residual_ppm) {
        *out_residual_ppm = residual_ppm;
    }

    return (residual_ppm <= profile->max_allowed_residual_ppm) ? 1 : 0;
}

int main(void) {
    // Verify hardware rdtscp counter is monotonic and active
    uint64_t t0 = read_hw_tsc();
    for (volatile int i = 0; i < 10000; i++) {}
    uint64_t t1 = read_hw_tsc();

    if (t1 <= t0) {
        printf("[FAIL] Hardware TSC counter did not advance.\n");
        return 1;
    }

    printf("=== APEX MOBILITY: RDTSC PHYSICAL-LAYER CAN INTRUSION FINGERPRINTER ===\n");
    printf("[SIL-TSC] Hardware RDTSCP Delta : %llu CPU cycles\n", (unsigned long long)(t1 - t0));

    // Genuine BMS ECU profile calibrated at 25°C (10 ms broadcast = 30,000,000 cycles @ 3.0 GHz)
    EcuClockProfile bms_ecu = {
        .baseline_period_cycles = 30000000.0,
        .baseline_temp_c = 25.0,
        .thermal_coeff_ppm_per_c = 0.8,
        .max_allowed_residual_ppm = 12.0
    };

    // Case 1: Genuine BMS operating in hot 48°C summer weather (+18.4 ppm thermal drift)
    double hot_weather_cycles = 30000000.0 * (1.0 + 19.5e-6);
    double residual_1 = 0.0;
    int valid_1 = verify_ecu_physical_fingerprint(&bms_ecu, hot_weather_cycles, 48.0, &residual_1);
    printf("[Test 1] Hot Weather (48°C) Genuine ECU -> Residual=%.2f ppm | Auth=%s\n",
           residual_1, valid_1 ? "ACCEPTED" : "REJECTED");

    // Case 2: Spoofed CAN frame injected by rogue infotainment MCU (+85 ppm crystal mismatch)
    double spoofed_cycles = 30000000.0 * (1.0 + 85.0e-6);
    double residual_2 = 0.0;
    int valid_2 = verify_ecu_physical_fingerprint(&bms_ecu, spoofed_cycles, 48.0, &residual_2);
    printf("[Test 2] Rogue Infotainment Spoof Frame  -> Residual=%.2f ppm | Auth=%s\n",
           residual_2, valid_2 ? "ACCEPTED" : "REJECTED");

    if (valid_1 == 1 && valid_2 == 0) {
        printf("\n[PASS] Hardware TSC fingerprinter tolerated thermal drift and blocked spoofed ECU.\n");
        return 0;
    }

    printf("\n[FAIL] Physical-layer ECU fingerprinting failed boundary test.\n");
    return 1;
}
