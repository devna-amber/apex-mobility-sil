#!/usr/bin/env python3
import sys
import numpy as np

class KalmanRangeEstimator:
    def __init__(self, initial_dist_m: float, initial_vel_mps: float):
        self.x = np.array([[initial_dist_m], [initial_vel_mps]], dtype=float)
        self.P = np.eye(2) * 1.0
        self.Q = np.array([[0.05, 0.0], [0.0, 0.1]])
        self.H = np.array([[1.0, 0.0]])

    def predict(self, dt: float) -> None:
        F = np.array([[1.0, dt], [0.0, 1.0]])
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + self.Q

    def update(self, measured_dist_m: float, sensor_variance: float) -> None:
        R = np.array([[sensor_variance]])
        y = np.array([[measured_dist_m]]) - (self.H @ self.x)
        S = self.H @ self.P @ self.H.T + R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + (K @ y)
        self.P = (np.eye(2) - (K @ self.H)) @ self.P

    @property
    def estimated_distance(self) -> float:
        return float(next(iter(self.x.flat)))

    @property
    def estimated_rel_velocity(self) -> float:
        it = iter(self.x.flat)
        next(it)
        return float(next(it))

def compute_aeb_command(distance_m: float, rel_velocity_mps: float) -> tuple[str, float, float]:
    if rel_velocity_mps >= -0.1:
        return "CLEAR", float("inf"), 0.0
    ttc = distance_m / abs(rel_velocity_mps)
    if ttc <= 1.2 or distance_m <= 6.0:
        return "EMERGENCY_BRAKE_FULL", ttc, 100.0
    elif ttc <= 2.5:
        return "FORWARD_COLLISION_WARNING", ttc, 45.0
    else:
        return "NOMINAL_CRUISE", ttc, 0.0

def main() -> int:
    dt = 0.1
    rng = np.random.default_rng(seed=101)
    true_dist = 45.0
    rel_vel = -25.0
    kf = KalmanRangeEstimator(initial_dist_m=46.0, initial_vel_mps=-24.0)
    aeb_triggered = False

    print("=== APEX MOBILITY AV: RADAR + LIDAR KALMAN FUSION & AEB ===")
    for step in range(1, 13):
        true_dist += rel_vel * dt
        radar_meas = true_dist + rng.normal(0.0, np.sqrt(1.2))
        lidar_meas = true_dist + rng.normal(0.0, np.sqrt(0.15))
        kf.predict(dt)
        kf.update(radar_meas, sensor_variance=1.2)
        kf.update(lidar_meas, sensor_variance=0.15)
        est_d = kf.estimated_distance
        est_v = kf.estimated_rel_velocity
        status, ttc, brake_pct = compute_aeb_command(est_d, est_v)
        ttc_str = f"{ttc:.2f}s" if np.isfinite(ttc) else "INF"
        print(f"[t={step*dt:4.1f}s] True={true_dist:5.2f}m | Fused={est_d:5.2f}m | TTC={ttc_str:>5} | State={status:<25} | Brake={brake_pct:5.1f}%")
        if status == "EMERGENCY_BRAKE_FULL":
            aeb_triggered = True
            break

    if aeb_triggered:
        print("\n[PASS] Kalman sensor fusion detected cut-in hazard and triggered AEB.")
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
