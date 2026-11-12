# Apex Mobility SIL — Autonomous Vehicle & EV Telemetry Architecture
![CI Status](https://github.com)
A deterministic, multi-layer Software-in-the-Loop (SIL) simulation and validation platform for EV powertrains and AV telemetry pipelines built using C, x86-64 Assembly, Verilog RTL, Python DSP, and GitHub Actions CI/CD.

## End-to-End Architecture Flow
- **(4) Python FIR & FFT DSP Filter** (Strips 450 Hz PWM inverter noise)
- **(2) x86-64 Assembly Checksum** (Zero-overhead frame verification)
- **(5) Predictive Thermal Digital Twin** (Forecasts core cell temp 60s ahead)
- **(1) Embedded C BMS Fault Guard** (Evaluates pack limits & logs DTCs)
- **(3) Verilog Hardware Safety FSM** (Single-cycle HV contactor trip)

## Quick Start on Ubuntu
```bash
sudo apt update && sudo apt install -y gcc nasm make iverilog python3-numpy
python3 scripts/run_sil_pipeline.py
```
