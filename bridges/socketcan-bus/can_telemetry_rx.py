#!/usr/bin/env python3
import socket
import struct
import sys

CAN_FRAME_FMT = "=IB3x8s"
CAN_FRAME_SIZE = struct.calcsize(CAN_FRAME_FMT)

def compute_can_crc8(data: bytes) -> int:
    crc = 0xFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1D) & 0xFF if (crc & 0x80) else (crc << 1) & 0xFF
    return crc

def main() -> int:
    interface = sys.argv[1] if len(sys.argv) > 1 else "vcan0"
    expected_frames = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    try:
        sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        sock.settimeout(3.0)
        sock.bind((interface,))
    except OSError as exc:
        print(f"[ERROR] Failed to bind SocketCAN interface '{interface}': {exc}")
        return 1

    received = 0
    while received < expected_frames:
        try:
            raw_frame = sock.recv(CAN_FRAME_SIZE)
        except socket.timeout:
            print("[FAIL] Timed out waiting for CAN frames.")
            sock.close()
            return 1

        can_id, can_dlc, data = struct.unpack(CAN_FRAME_FMT, raw_frame)
        if can_id != 0x101 or can_dlc != 8:
            continue

        expected_crc = compute_can_crc8(data[:7])
        actual_crc = data[7]
        if expected_crc != actual_crc:
            print(f"[FAIL] CRC mismatch on frame {received}")
            sock.close()
            return 1

        voltage_v = struct.unpack(">H", data[0:2])[0] / 10.0
        current_a = struct.unpack(">h", data[2:4])[0] / 10.0
        soc = data[4]
        temp_c = data[5]
        counter = data[6]

        print(f"[PY-CAN-RX] Verified Frame #{counter} | Pack={voltage_v:.1f}V | Curr={current_a:.1f}A | SoC={soc}% | Temp={temp_c}C [CRC OK]")
        received += 1

    sock.close()
    print("[PASS] All SocketCAN frames received and verified.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
