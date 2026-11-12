#!/usr/bin/env python3
import os
import subprocess
import sys

def has_vcan0() -> bool:
    return os.path.exists("/sys/class/net/vcan0")

STEPS = [
    ("1. C BMS Fault Guard", "gcc -O2 ecu-powertrain-c/bms_fault_guard.c -o /tmp/bms_guard && /tmp/bms_guard && rm -f /tmp/bms_guard"),
    ("2. x86-64 Assembly Checksum", "make -C bridges/checksum-asm test && make -C bridges/checksum-asm clean"),
    ("3. Verilog BMS Hardware Interlock", "make -C plant-models/safety-fsm-verilog test && make -C plant-models/safety-fsm-verilog clean"),
    ("4. Python FIR & FFT DSP Filter", "python3 telemetry/dsp-filter/signal_conditioning.py"),
    ("5. Predictive Thermal Digital Twin", "python3 plant-models/thermal-twin/thermal_predictor.py"),
]

def main() -> int:
    print("=== APEX MOBILITY SIL: FULL 6-LAYER VALIDATION ===")
    for name, cmd in STEPS:
        print(f"\n--- Running {name} ---")
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            print(f"[ERROR] Failed at: {name}")
            return result.returncode

    print("\n--- Running 6. Linux SocketCAN (vcan0) Bridge ---")
    if has_vcan0():
        can_cmd = "make -C bridges/socketcan-bus test && make -C bridges/socketcan-bus clean"
    else:
        print("[INFO] vcan0 interface not active locally; verifying C SocketCAN compilation...")
        can_cmd = "make -C bridges/socketcan-bus && make -C bridges/socketcan-bus clean"

    result = subprocess.run(can_cmd, shell=True)
    if result.returncode != 0:
        print("[ERROR] Failed at: 6. Linux SocketCAN Bridge")
        return result.returncode

    print("\n=== ALL 6 SIL LAYERS PASSED SUCCESSFULLY ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
