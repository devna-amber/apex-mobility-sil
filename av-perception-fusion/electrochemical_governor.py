#!/usr/bin/env python3
"""
av-perception-fusion/electrochemical_governor.py
Electrochemical-Aware Autonomous Trajectory & Regenerative Braking Governor.
Co-optimizes AV deceleration profiles with battery anode lithium-plating physics
while preserving a hard safety override for sudden road hazards.
"""

import sys
import numpy as np


def compute_anode_overpotential_mv(regen_current_a: float, cell_temp_c: float, soc_pct: float) -> float:
    """
    Simplified electrochemical anode surface overpotential model (mV).
    Negative overpotential (< 0 mV) indicates lithium plating risk on graphite anodes,
    especially during high-current regen at high SoC or low temperatures.
    """
    # Equilibrium potential drops near 100% SoC
    equilibrium_mv = max(15.0, 140.0 * (1.0 - (soc_pct / 105.0)))
    # Charge-transfer resistance increases sharply at colder temperatures
    temp_factor = np.exp(0.035 * (25.0 - cell_temp_c))
    polarization_drop_mv = 0.55 * regen_current_a * temp_factor
    return float(equilibrium_mv - polarization_drop_mv)


def plan_braking_split(
    required_decel_mps2: float,
    vehicle_speed_mps: float,
    ttc_sec: float,
    cell_temp_c: float,
    soc_pct: float,
) -> dict:
    """
    Determines optimal split between Regenerative Braking (charges battery)
    and Mechanical Friction Braking (dissipates heat safely) to prevent Li-plating.
    """
    vehicle_mass_kg = 1850.0
    pack_voltage_v = 400.0

    # Total braking power required (Watts)
    braking_force_n = vehicle_mass_kg * required_decel_mps2
    braking_power_w = braking_force_n * vehicle_speed_mps
    unconstrained_regen_a = braking_power_w / pack_voltage_v

    # Check if full regenerative braking would trigger lithium plating (< 0 mV)
    raw_overpotential = compute_anode_overpotential_mv(unconstrained_regen_a, cell_temp_c, soc_pct)

    # Hard Safety Override: If Time-to-Collision < 1.3s, safety overrides battery health
    if ttc_sec < 1.3:
        return {
            "mode": "SAFETY_AEB_OVERRIDE",
            "regen_current_a": unconstrained_regen_a,
            "friction_brake_pct": 100.0,
            "anode_overpotential_mv": raw_overpotential,
            "plating_prevented": False,
        }

    # Electrochemical Optimization: Cap regen current so anode overpotential stays >= +10 mV
    safe_regen_a = unconstrained_regen_a
    while (
        safe_regen_a > 0.0
        and compute_anode_overpotential_mv(safe_regen_a, cell_temp_c, soc_pct) < 10.0
    ):
        safe_regen_a -= 5.0

    safe_regen_a = max(0.0, safe_regen_a)
    regen_ratio = (safe_regen_a / unconstrained_regen_a) if unconstrained_regen_a > 0 else 1.0
    friction_blend_pct = (1.0 - regen_ratio) * 100.0
    final_overpotential = compute_anode_overpotential_mv(safe_regen_a, cell_temp_c, soc_pct)

    return {
        "mode": "ELECTROCHEMICAL_BLENDED_REGEN",
        "regen_current_a": safe_regen_a,
        "friction_brake_pct": friction_blend_pct,
        "anode_overpotential_mv": final_overpotential,
        "plating_prevented": raw_overpotential < 0.0 and final_overpotential >= 10.0,
    }


def main() -> int:
    print("=== APEX MOBILITY: ELECTROCHEMICAL-AWARE AV TRAJECTORY GOVERNOR ===")

    # Scenario 1: High-SoC (92%) highway deceleration where full regen causes Li-plating
    res_eco = plan_braking_split(
        required_decel_mps2=3.2,
        vehicle_speed_mps=24.0,
        ttc_sec=4.5,
        cell_temp_c=18.0,
        soc_pct=92.0,
    )
    print("\n[Scenario 1] Planned Highway Deceleration at 92% SoC (18°C)")
    print(f" -> Mode                : {res_eco['mode']}")
    print(f" -> Capped Regen Current: {res_eco['regen_current_a']:.1f} A")
    print(f" -> Friction Brake Blend: {res_eco['friction_brake_pct']:.1f}%")
    print(f" -> Anode Overpotential : +{res_eco['anode_overpotential_mv']:.2f} mV (Safe > 0 mV)")

    # Scenario 2: Sudden obstacle cut-in (TTC = 0.9s) -> Safety overrides battery longevity
    res_aeb = plan_braking_split(
        required_decel_mps2=7.5,
        vehicle_speed_mps=22.0,
        ttc_sec=0.9,
        cell_temp_c=18.0,
        soc_pct=92.0,
    )
    print("\n[Scenario 2] Sudden Local Cut-In Hazard (TTC = 0.9s)")
    print(f" -> Mode                : {res_aeb['mode']}")
    print(f" -> Friction Brake Force: {res_aeb['friction_brake_pct']:.1f}% (Crash Avoidance Priority)")

    if res_eco["plating_prevented"] and res_aeb["mode"] == "SAFETY_AEB_OVERRIDE":
        print("\n[PASS] Governor prevented Li-plating during normal driving and preserved AEB safety override.")
        return 0

    print("\n[FAIL] Electrochemical governor failed boundary validation.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
