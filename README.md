# Apex Mobility SIL — Autonomous Vehicle & EV Telemetry Architecture

A Software-in-the-Loop (SIL) simulation of fault-tolerant Electronic Control Units (ECUs) built in C, Python, and Linux.

## Modules
* **`/ecu-powertrain-c`**: Deterministic Battery Management System (BMS) fault guard that monitors pack voltage, cell temperature, and discharge current, isolating the high-voltage contactor and logging Diagnostic Trouble Codes (DTCs) on critical anomalies.
* **`/ecu-cabin-vision`**: *(Upcoming)* Edge-AI driver attention and anti-tamper sentinel.
* **`/linux-watchdog`**: *(Upcoming)* Multi-process heartbeat supervisor for ASIL-style fault recovery.
