#!/usr/bin/env python3
import os
import subprocess
import sys

def has_vcan0() -> bool:
    return os.path.exists("/sys/class/net/vcan0")

STEPS = [
    ("1. C BMS Fault Guard", "gcc -O2 ecu-powertrain-c/bms_fault_guard.c -o /tmp/bms_guard && /tmp/bms_guard && rm -f /tmp/bms_guard"),
    ("2. x86-64 Assembly Checksum", "make -C bridges/checksum-asm test && make -C bridges/checksum-asm clean"),
    ("3. x86-64 RDTSCP CAN Clock-Skew Fingerprinter", "make -C bridges/can-phy-fingerprint test && make -C bridges/can-phy-fingerprint clean"),
    ("4. Verilog BMS Hardware Interlock FSM", "make -C plant-models/safety-fsm-verilog test && make -C plant-models/safety-fsm-verilog clean"),
    ("5. Verilog Self-Healing Cell-Bypass Matrix", "make -C plant-models/self-healing-reflex test && make -C plant-models/self-healing-reflex clean"),
    ("6. Python FIR & FFT DSP Filter", "python3 telemetry/dsp-filter/signal_conditioning.py"),
    ("7. Predictive Thermal Digital Twin", "python3 plant-models/thermal-twin/thermal_predictor.py"),
    ("8. AV Radar+LiDAR Kalman Fusion & AEB", "python3 av-perception-fusion/sensor_fusion_aeb.py"),
    ("9. Electrochemical-Aware AV Trajectory Governor", "python3 av-perception-fusion/electrochemical_governor.py"),
    ("10. Frontier Edge-Case & Boundary Stress Suite", "python3 scenarios/edge-case-stress/edge_case_stress_suite.py"),
]

def main() -> int:
    print("=== APEX MOBILITY SIL: FULL 11-LAYER ARCHITECTURE VALIDATION ===")
    for name, cmd in STEPS:
        print(f"\n--- Running {name} ---")
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            print(f"[ERROR] Failed at: {name}")
            return result.returncode

    print("\n--- Running 11. Linux SocketCAN (vcan0) Bridge ---")
    if has_vcan0():
        can_cmd = "make -C bridges/socketcan-bus test && make -C bridges/socketcan-bus clean"
    else:
        print("[INFO] vcan0 interface not active locally; verifying C SocketCAN compilation...")
        can_cmd = "make -C bridges/socketcan-bus && make -C bridges/socketcan-bus clean"

    result = subprocess.run(can_cmd, shell=True)
    if result.returncode != 0:
        print("[ERROR] Failed at: 11. Linux SocketCAN Bridge")
        return result.returncode

    print("\n=== ALL 11 SIL LAYERS PASSED SUCCESSFULLY ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
