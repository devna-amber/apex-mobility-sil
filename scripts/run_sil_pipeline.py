#!/usr/bin/env python3
import subprocess
import sys

STEPS = [
    ("1. C BMS Fault Guard", "gcc -O2 ecu-powertrain-c/bms_fault_guard.c -o /tmp/bms_guard && /tmp/bms_guard && rm -f /tmp/bms_guard"),
    ("2. x86-64 Assembly Checksum", "make -C bridges/checksum-asm test && make -C bridges/checksum-asm clean"),
    ("3. Verilog BMS Hardware Interlock", "make -C plant-models/safety-fsm-verilog test && make -C plant-models/safety-fsm-verilog clean"),
    ("4. Python FIR & FFT DSP Filter", "python3 telemetry/dsp-filter/signal_conditioning.py"),
]

def main() -> int:
    print("=== APEX MOBILITY SIL: END-TO-END VALIDATION ===")
    for name, cmd in STEPS:
        print(f"\n--- Running {name} ---")
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            print(f"[ERROR] Failed at: {name}")
            return result.returncode
    print("\n=== ALL 4 SIL LAYERS PASSED SUCCESSFULLY ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
