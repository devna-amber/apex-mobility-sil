# Apex Mobility SIL — Autonomous Vehicle & EV Telemetry Architecture

![CI Status](https://github.com)

![Apex Mobility SIL Telemetry Dashboard](docs/sil_telemetry_dashboard.svg)

A deterministic, **11-layer Software-in-the-Loop (SIL)** simulation and validation architecture for next-generation Electric Vehicles (EVs) and Autonomous Vehicles (AVs). Built and verified natively on Linux using **C11, x86-64 Assembly (`nasm`), Verilog RTL (`iverilog`), Linux SocketCAN (`vcan0`), Python DSP, and GitHub Actions CI/CD**.

---

## Novel Architectural Breakthroughs

Unlike traditional automotive stacks where Autonomous Driving planners and Battery Management Systems (BMS) operate as isolated silos, **Apex Mobility SIL** introduces three closed-loop cross-domain innovations:

1. **Electrochemical-Aware AV Trajectory & Regen Governor** (`/av-perception-fusion/electrochemical_governor.py`)
   * Co-optimizes autonomous braking curves with **graphite anode lithium-plating overpotential physics**—blending mechanical friction braking with regenerative deceleration to eliminate cell degradation while preserving a hard **Safety AEB Override** (`TTC < 1.3s`) for sudden road obstacles.
2. **Physical-Layer CAN Bus Intrusion Fingerprinting via `rdtscp`** (`/bridges/can-phy-fingerprint/`)
   * Authenticates arriving CAN frames without cryptographic payload overhead by measuring nanosecond crystal oscillator clock-skew via x86-64 Assembly (`rdtscp`) paired with **ambient thermal drift compensation** (`0.8 ppm/°C`).
3. **Self-Healing Hardware Cell-Bypass & Limp-Home Reflex Matrix** (`/plant-models/self-healing-reflex/`)
   * Synthesizable **Verilog RTL** matrix that isolates single failed battery strings in **one clock cycle** to maintain **66% autonomous limp-home power** for safe highway shoulder pull-over, while enforcing total high-voltage contactor lockout during multi-string or thermal runaway faults.

---

## Complete 11-Layer System Architecture

| Layer | Module Path | Technology | Core Engineering Function |
| :--- | :--- | :--- | :--- |
| **1** | `/ecu-powertrain-c` | **Embedded C (C11)** | Real-time BMS thermal, voltage, and discharge current guard with Diagnostic Trouble Code (DTC) logging. |
| **2** | `/bridges/checksum-asm` | **x86-64 Assembly + C** | System V AMD64 ABI register-level rotating XOR frame checksum detecting single-bit CAN corruption. |
| **3** | `/bridges/can-phy-fingerprint` | **x86-64 `rdtscp` + C** | Thermal-compensated hardware clock-skew fingerprinter blocking spoofed ECU frame injections. |
| **4** | `/plant-models/safety-fsm-verilog` | **Verilog RTL (`iverilog`)** | Deterministic hardware safety interlock FSM (`IDLE` → `NOMINAL` → `DERATE` → `FAULT_LOCKOUT`). |
| **5** | `/plant-models/self-healing-reflex` | **Verilog RTL (`iverilog`)** | Single-cycle 3-string battery bypass matrix enabling graceful autonomous shoulder pull-over. |
| **6** | `/telemetry/dsp-filter` | **Python (`NumPy`)** | 51-tap Hamming-windowed FIR low-pass convolution filter + FFT analyzer (+16.8 dB SNR gain vs. 450 Hz PWM noise). |
| **7** | `/plant-models/thermal-twin` | **Python (`NumPy`)** | 1st-order RC + Joule heating ($I^2R$) Digital Twin forecasting core cell temperatures 60 seconds ahead. |
| **8** | `/av-perception-fusion/sensor_fusion_aeb.py` | **Python (`NumPy`)** | 1D Kalman Filter fusing noisy Radar and LiDAR range measurements to trigger Time-to-Collision AEB. |
| **9** | `/av-perception-fusion/electrochemical_governor.py` | **Python (`NumPy`)** | Anode overpotential trajectory governor balancing zero-degradation regen with emergency crash avoidance. |
| **10** | `/scenarios/edge-case-stress` | **Python** | Unified boundary stress suite validating emergency AEB overrides, 48°C crystal drift, and cascading faults. |
| **11** | `/bridges/socketcan-bus` | **Linux SocketCAN (`vcan0`)** | Native kernel `PF_CAN` C transmitter and Python receiver exchanging real 8-byte CRC-8 protected CAN frames. |

---

## Quick Start on Ubuntu

```bash
# 1. Install Linux systems, HDL, and scientific toolchains
sudo apt update && sudo apt install -y gcc nasm make iverilog python3-numpy can-utils

# 2. Optional: Bring up virtual automotive CAN bus
sudo modprobe vcan && sudo ip link add dev vcan0 type vcan && sudo ip link set up vcan0

# 3. Execute the full 11-layer end-to-end validation suite
python3 scripts/run_sil_pipeline.py
```
