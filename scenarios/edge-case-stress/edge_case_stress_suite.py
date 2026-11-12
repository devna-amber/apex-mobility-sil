#!/usr/bin/env python3
import sys

def evaluate_regen_governor(ttc_sec: float, requested_regen_kw: float, cell_temp_c: float) -> dict:
    max_safe_regen_kw = 65.0 if cell_temp_c > 42.0 else 110.0
    if ttc_sec < 1.3:
        return {
            "mode": "SAFETY_AEB_OVERRIDE",
            "regen_kw": requested_regen_kw,
            "friction_brake_pct": 100.0,
            "plating_risk": True,
        }
    elif requested_regen_kw > max_safe_regen_kw:
        blended_friction = ((requested_regen_kw - max_safe_regen_kw) / requested_regen_kw) * 100.0
        return {
            "mode": "ELECTROCHEMICAL_BLENDED",
            "regen_kw": max_safe_regen_kw,
            "friction_brake_pct": round(blended_friction, 1),
            "plating_risk": False,
        }
    return {
        "mode": "PURE_REGEN_OPTIMAL",
        "regen_kw": requested_regen_kw,
        "friction_brake_pct": 0.0,
        "plating_risk": False,
    }

def evaluate_can_clock_skew(measured_skew_ppm: float, ambient_temp_c: float) -> str:
    nominal_temp_c = 25.0
    expected_thermal_drift_ppm = (ambient_temp_c - nominal_temp_c) * 0.8
    residual_skew_ppm = abs(measured_skew_ppm - expected_thermal_drift_ppm)
    return "AUTHENTIC_ECU" if residual_skew_ppm <= 12.0 else "INTRUSION_SPOOF_DETECTED"

def evaluate_self_healing_pack(failed_strings: int, max_cell_temp_c: float) -> dict:
    if max_cell_temp_c >= 65.0 or failed_strings >= 2:
        return {
            "hv_contactor": "OPEN_LOCKOUT",
            "av_action": "IMMEDIATE_IN_LANE_STOP",
            "available_power_pct": 0,
        }
    elif failed_strings == 1:
        return {
            "hv_contactor": "BYPASS_STRING_1",
            "av_action": "AUTONOMOUS_SHOULDER_LIMP_HOME",
            "available_power_pct": 60,
        }
    return {
        "hv_contactor": "CLOSED_ALL_STRINGS",
        "av_action": "NOMINAL_OPERATION",
        "available_power_pct": 100,
    }

def main() -> int:
    print("=== APEX MOBILITY SIL: EDGE-CASE & BOUNDARY STRESS SUITE ===\n")

    res_1a = evaluate_regen_governor(ttc_sec=4.5, requested_regen_kw=120.0, cell_temp_c=45.0)
    assert res_1a["mode"] == "ELECTROCHEMICAL_BLENDED" and not res_1a["plating_risk"]
    print(f"[PASS 1A] Warm-Pack High Regen   -> {res_1a['mode']} (Regen={res_1a['regen_kw']}kW, Friction={res_1a['friction_brake_pct']}%)")

    res_1b = evaluate_regen_governor(ttc_sec=0.9, requested_regen_kw=120.0, cell_temp_c=45.0)
    assert res_1b["mode"] == "SAFETY_AEB_OVERRIDE" and res_1b["friction_brake_pct"] == 100.0
    print(f"[PASS 1B] Sudden Cut-In (TTC 0.9s)-> {res_1b['mode']} (Safety overrides cell plating limit)")

    res_2a = evaluate_can_clock_skew(measured_skew_ppm=21.0, ambient_temp_c=48.0)
    assert res_2a == "AUTHENTIC_ECU"
    print(f"[PASS 2A] 48°C Thermal Clock Drift -> {res_2a} (No false intrusion alarm)")

    res_2b = evaluate_can_clock_skew(measured_skew_ppm=85.0, ambient_temp_c=48.0)
    assert res_2b == "INTRUSION_SPOOF_DETECTED"
    print(f"[PASS 2B] Rogue ECU Frame Injection -> {res_2b} (Blocked via residual clock-skew)")

    res_3a = evaluate_self_healing_pack(failed_strings=1, max_cell_temp_c=48.0)
    assert res_3a["hv_contactor"] == "BYPASS_STRING_1" and res_3a["available_power_pct"] == 60
    print(f"[PASS 3A] Single String Fault       -> {res_3a['hv_contactor']} ({res_3a['av_action']})")

    res_3b = evaluate_self_healing_pack(failed_strings=2, max_cell_temp_c=68.0)
    assert res_3b["hv_contactor"] == "OPEN_LOCKOUT" and res_3b["available_power_pct"] == 0
    print(f"[PASS 3B] Cascading Thermal Fault   -> {res_3b['hv_contactor']} ({res_3b['av_action']})")

    print("\n=== ALL BOUNDARY & EDGE-CASE STRESS TESTS PASSED ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
