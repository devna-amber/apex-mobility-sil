#include <stdio.h>
#include <stdint.h>
#include <stddef.h>

extern uint32_t compute_telemetry_checksum(const uint8_t *data, size_t length);

typedef struct __attribute__((packed)) {
    uint16_t pack_voltage_dv;
    int16_t  pack_current_da;
    uint8_t  soc_percent;
    uint8_t  max_cell_temp_c;
    uint16_t motor_rpm;
    uint32_t timestamp_ms;
} EvTelemetryFrame;

int main(void) {
    EvTelemetryFrame frame = {4020, 185, 84, 36, 6400, 10500};
    const uint8_t *raw_bytes = (const uint8_t *)&frame;
    size_t frame_size = sizeof(EvTelemetryFrame);

    uint32_t valid_crc = compute_telemetry_checksum(raw_bytes, frame_size);
    printf("[SIL-ASM] Frame Size : %zu bytes\n", frame_size);
    printf("[SIL-ASM] Valid CRC  : 0x%08X\n", valid_crc);

    frame.max_cell_temp_c ^= 0x01;
    uint32_t corrupted_crc = compute_telemetry_checksum(raw_bytes, frame_size);
    printf("[SIL-ASM] Fault CRC  : 0x%08X\n", corrupted_crc);

    if (valid_crc != corrupted_crc) {
        printf("[PASS] Assembly integrity check detected single-bit telemetry corruption.\n");
        return 0;
    }
    return 1;
}
