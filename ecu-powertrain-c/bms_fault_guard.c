#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#define SLEEP_MS(ms) Sleep(ms)
#else
#include <unistd.h>
#define SLEEP_MS(ms) usleep((ms) * 1000)
#endif

// Automotive BMS Safety Thresholds (ISO 26262 style deterministic limits)
#define MAX_PACK_VOLTAGE   420.0f  // Volts
#define MIN_PACK_VOLTAGE   300.0f  // Volts
#define MAX_CELL_TEMP       55.0f  // Celsius (Thermal runaway threshold)
#define MAX_DISCHARGE_AMP  250.0f  // Amps (Over-current threshold)

// Diagnostic Trouble Codes (DTCs)
typedef enum {
    DTC_NONE          = 0x0000,
    DTC_OVER_VOLTAGE  = 0x10A1,
    DTC_UNDER_VOLTAGE = 0x10A2,
    DTC_OVER_TEMP     = 0x10A3,
    DTC_OVER_CURRENT  = 0x10A4
} FaultCode;

// Virtual ECU State Structure
typedef struct {
    float pack_voltage;
    float cell_temp;
    float current_draw;
    bool hv_contactor_closed;
    FaultCode active_fault;
} EVPowertrainECU;

// Deterministic Safety Evaluation Loop
void evaluate_safety(EVPowertrainECU *ecu) {
    if (ecu->cell_temp > MAX_CELL_TEMP) {
        ecu->active_fault = DTC_OVER_TEMP;
        ecu->hv_contactor_closed = false;
    } else if (ecu->current_draw > MAX_DISCHARGE_AMP) {
        ecu->active_fault = DTC_OVER_CURRENT;
        ecu->hv_contactor_closed = false;
    } else if (ecu->pack_voltage > MAX_PACK_VOLTAGE) {
        ecu->active_fault = DTC_OVER_VOLTAGE;
        ecu->hv_contactor_closed = false;
    } else if (ecu->pack_voltage < MIN_PACK_VOLTAGE) {
        ecu->active_fault = DTC_UNDER_VOLTAGE;
        ecu->hv_contactor_closed = false;
    }
}

void log_fault_to_file(int cycle, EVPowertrainECU ecu) {
    FILE *fp = fopen("dtc_blackbox.log", "a");
    if (fp != NULL) {
        fprintf(fp, "[CYCLE %03d] CRITICAL FAULT | DTC: 0x%X | V: %.1fV | T: %.1fC | I: %.1fA | HV_CONTACTOR: OPEN\n",
                cycle, ecu.active_fault, ecu.pack_voltage, ecu.cell_temp, ecu.current_draw);
        fclose(fp);
    }
}

int main() {
    srand((unsigned int)time(NULL));

    EVPowertrainECU ecu = {
        .pack_voltage = 398.5f,
        .cell_temp = 32.0f,
        .current_draw = 85.0f,
        .hv_contactor_closed = true,
        .active_fault = DTC_NONE
    };

    printf("=== APEX MOBILITY SIL: EV POWERTRAIN & BMS GUARD ===\n");
    printf("Monitoring High-Voltage Pack Telemetry...\n\n");

    for (int cycle = 1; cycle <= 15; cycle++) {
        // Simulate normal driving telemetry fluctuations
        ecu.pack_voltage = 395.0f + ((rand() % 100) / 10.0f);
        ecu.cell_temp += 1.4f;
        ecu.current_draw = 80.0f + (rand() % 40);

        // Inject a simulated thermal fault at Cycle 10
        if (cycle == 10) {
            printf(">>> [SIMULATION INJECT] Cooling pump failure! Rapid thermal spike...\n");
            ecu.cell_temp = 58.4f;
        }

        evaluate_safety(&ecu);

        printf("[Cycle %02d] Voltage: %.1fV | Temp: %.1fC | Current: %.1fA | Contactor: %s\n",
               cycle,
               ecu.pack_voltage,
               ecu.cell_temp,
               ecu.current_draw,
               ecu.hv_contactor_closed ? "CLOSED (ACTIVE)" : "OPEN (ISOLATED)");

        if (!ecu.hv_contactor_closed) {
            printf("\n[EMERGENCY SHUTDOWN] Fault Detected (DTC: 0x%X). High-Voltage Contactor Isolated!\n", ecu.active_fault);
            printf("Telemetry saved to 'dtc_blackbox.log'.\n");
            log_fault_to_file(cycle, ecu);
            break;
        }

        SLEEP_MS(400);
    }

    return 0;
}
