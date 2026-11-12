# Apex Mobility SIL — Autonomous Vehicle & EV Telemetry Architecture

[![Apex Mobility SIL Regression Gate](https://github.com)](https://github.com)

A deterministic, multi-layer **Software-in-the-Loop (SIL)** simulation and validation architecture for fault-tolerant Electric Vehicle (EV) powertrains and Autonomous Vehicle (AV) telemetry pipelines. Built and verified natively on Linux using **C, x86-64 Assembly, Verilog RTL, Python DSP, and GitHub Actions CI/CD**.

---

## System Architecture & Modules

| Layer | Module Path | Technology | Engineering Function |
| :--- | :--- | :--- | :--- |
| **1. Embedded ECU Control** | `/ecu-powertrain-c` | **C (C11)** | Deterministic Battery Management System (BMS) fault guard monitoring pack voltage, cell temperature, and discharge current to isolate HV contactors and log DTCs. |
| **2. Low-Level Frame Integrity** | `/bridges/checksum-asm` | **x86-64 Assembly (`nasm`) + C** | Register-level rotating XOR checksum routine adhering to the System V AMD64 ABI to detect single-bit CAN-FD telemetry corruption with zero overhead. |
| **3. Hardware Safety Interlock** | `/plant-models/safety-fsm-verilog` | **Verilog RTL (`iverilog`)** | Synthesizable Finite State Machine (`IDLE` → `NOMINAL` → `DERATE` → `FAULT_LOCKOUT`) providing single-cycle hardware contactor trip and latched fault protection. |
| **4. Signals & Systems Conditioning** | `/telemetry/dsp-filter` | **Python (`NumPy`)** | Discrete-time Hamming-windowed FIR low-pass convolution filter and FFT spectral analyzer attenuating 450 Hz PWM inverter switching noise (+16.8 dB SNR gain). |
| **5. Automated Regression Gate** | `/.github/workflows` | **GitHub Actions** | Headless CI/CD pipeline executing all C, Assembly, Verilog testbenches, and Python DSP assertions on every push to `main`. |

---

## Running Locally on Ubuntu

```bash
# Install dependencies
sudo apt update && sudo apt install -y gcc nasm make iverilog python3-numpy

# 1. Run C BMS Guard
gcc -O2 ecu-powertrain-c/bms_fault_guard.c -o bms_guard && ./bms_guard && rm bms_guard

# 2. Run x86-64 Assembly Checksum Verification
make -C bridges/checksum-asm test

# 3. Run Verilog BMS Hardware Interlock Testbench
make -C plant-models/safety-fsm-verilog test

# 4. Run Python DSP Telemetry Filter
python3 telemetry/dsp-filter/signal_conditioning.py
```
