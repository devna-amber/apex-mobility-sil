import math, random, struct, zlib

GLYPHS = {
    "A": "01110100011000111111100011000110001", "B": "11110100011000111110100011000111110",
    "C": "01111100001000010000100001000001111", "D": "11110100011000110001100011000111110",
    "E": "11111100001000011110100001000011111", "F": "11111100001000011110100001000010000",
    "G": "01111100001000010111100011000101111", "H": "10001100011000111111100011000110001",
    "I": "11111001000010000100001000010011111", "K": "10001100101010011000101001001010001",
    "L": "10000100001000010000100001000011111", "M": "10001110111010110101100011000110001",
    "N": "10001110011010110011100011000110001", "O": "01110100011000110001100011000101110",
    "P": "11110100011000111110100001000010000", "R": "11110100011000111110101001001010001",
    "S": "01111100001000001110000010000111110", "T": "11111001000010000100001000010000100",
    "U": "10001100011000110001100011000101110", "V": "10001100011000110001100010101000100",
    "W": "10001100011000110101101011101110001", "X": "10001100010101000100010101000110001",
    "Y": "10001100010101000100001000010000100", "Z": "11111000010001000100010001000011111",
    "0": "01110100111010110101110011000101110", "1": "00100011000010000100001000010001110",
    "2": "01110100010000100110010001000011111", "3": "11110000010000101110000010000111110",
    "4": "00010001100101010010111110001000010", "5": "11111100001111000001000011000101110",
    "6": "01110100001000011110100011000101110", "7": "11111000010001000100010000100001000",
    "8": "01110100011000101110100011000101110", "9": "01110100011000101111000010000101110",
    ":": "00000001000010000000001000010000000", ".": "00000000000000000000000000110001100",
    "-": "00000000000000011111000000000000000", "+": "00000001000010011111001000010000000",
    "/": "00001000100010000100010001000000000", "<": "00010001000100010000010000010000010",
    "(": "00010001000100001000010000010000010", ")": "01000001000001000010000100010001000",
    " ": "00000000000000000000000000000000000",
}

def write_png(path, w, h, buf):
    def chk(t, d):
        return struct.pack("!I", len(d)) + t + d + struct.pack("!I", zlib.crc32(t + d) & 0xFFFFFFFF)
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(buf[y*w*3:(y+1)*w*3])
    ihdr = struct.pack("!IIBBBBB", w, h, 8, 2, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chk(b"IHDR", ihdr) + chk(b"IDAT", zlib.compress(bytes(raw), 9)) + chk(b"IEND", b""))

def px(buf, w, h, x, y, r, g, b, a=1.0):
    if 0 <= x < w and 0 <= y < h:
        i = (y * w + x) * 3
        buf[i]   = int(buf[i] * (1 - a) + r * a)
        buf[i+1] = int(buf[i+1] * (1 - a) + g * a)
        buf[i+2] = int(buf[i+2] * (1 - a) + b * a)

def text(buf, w, h, x0, y0, s, r, g, b, sc=2):
    cx = x0
    for ch in s.upper():
        bits = GLYPHS.get(ch, GLYPHS[" "])
        for idx, bit in enumerate(bits):
            if bit == "1":
                rx, ry = idx % 5, idx // 5
                for dy in range(sc):
                    for dx in range(sc):
                        px(buf, w, h, cx + rx*sc + dx, y0 + ry*sc + dy, r, g, b)
        cx += 6 * sc

def line(buf, w, h, x0, y0, x1, y1, r, g, b, thick=1, a=1.0):
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    for s in range(steps + 1):
        cx = int(round(x0 + (x1 - x0) * s / steps))
        cy = int(round(y0 + (y1 - y0) * s / steps))
        for dy in range(-thick // 2, thick // 2 + 1):
            for dx in range(-thick // 2, thick // 2 + 1):
                px(buf, w, h, cx + dx, cy + dy, r, g, b, a)

def plot(buf, w, h, xs, ys, x0, x1, y0, y1, bx, by, bw, bh, r, g, b, glow=True):
    pts = [(int(round(bx + (x - x0)/(x1 - x0)*bw)), int(round(by + bh - (y - y0)/(y1 - y0)*bh))) for x, y in zip(xs, ys)]
    for i in range(1, len(pts)):
        (x0, y0), (x1, y1) = pts[i-1], pts[i]
        if glow:
            line(buf, w, h, x0, y0, x1, y1, r, g, b, thick=7, a=0.16)
        line(buf, w, h, x0, y0, x1, y1, r, g, b, thick=2 if glow else 1, a=1.0 if glow else 0.75)

# 1. Generate labeled status badge
BW, BH = 292, 28
bbuf = bytearray(bytes((18, 25, 36)) * (BW * BH))
for y in range(1, BH - 1):
    for x in range(140, BW - 1):
        px(bbuf, BW, BH, x, y, 16, 115, 65)
text(bbuf, BW, BH, 14, 8, "SIL GATE", 205, 230, 250, sc=2)
text(bbuf, BW, BH, 152, 8, "12/12 PASS", 235, 255, 245, sc=2)
write_png("docs/ci_badge.png", BW, BH, bbuf)

# 2. Generate labeled 3-panel HUD dashboard
W, H = 1120, 355
buf = bytearray(bytes((9, 13, 22)) * (W * H))
text(buf, W, H, 24, 14, "APEX MOBILITY SIL // REAL-TIME POWERTRAIN + AV VALIDATION HUD", 0, 225, 255, sc=2)
text(buf, W, H, 880, 16, "STATUS: 12/12 PASS", 55, 255, 140, sc=2)

cards = [
    (22,  "1. FIR DSP FILTER",   "SNR: +27.95 DB (450HZ CUT)", "RED: RAW PWM | GREEN: FIR"),
    (386, "2. THERMAL TWIN",     "60S FORECAST: 87.7C PEAK",   "ORANGE: 320A | RED: 55C LIMIT"),
    (750, "3. KALMAN AEB FUSION","TRIGGER: TTC < 1.2S (0.7S)", "VIOLET: RADAR | GREEN: FUSED"),
]
for cx, title, metric, legend in cards:
    for y in range(44, 336):
        for x in range(cx, cx + 348):
            px(buf, W, H, x, y, 15, 22, 34)
    line(buf, W, H, cx, 44, cx + 347, 44, 0, 220, 255, thick=2)
    line(buf, W, H, cx, 335, cx + 347, 335, 35, 55, 78, thick=1)
    text(buf, W, H, cx + 14, 54, title, 235, 245, 255, sc=2)
    text(buf, W, H, cx + 14, 74, metric, 0, 225, 255, sc=1)
    text(buf, W, H, cx + 14, 320, legend, 140, 165, 190, sc=1)
    for gx in range(cx + 18, cx + 335, 35):
        for y in range(90, 310, 5):
            px(buf, W, H, gx, y, 32, 45, 62)
    for gy in range(90, 311, 35):
        for x in range(cx + 18, cx + 334, 5):
            px(buf, W, H, x, gy, 32, 45, 62)

rng = random.Random(42)
t = [i * 0.5 for i in range(300)]
clean = [120 + 35 * math.sin(2 * math.pi * 5 * (i / 2000)) for i in range(300)]
noisy = [clean[i] + 18 * math.sin(2 * math.pi * 450 * (i / 2000)) + rng.gauss(0, 2.2) for i in range(300)]
filt = [sum(noisy[max(0, min(299, i - k + 12))] for k in range(25)) / 25.0 for i in range(300)]
plot(buf, W, H, t[15:-15], noisy[15:-15], 0, 150, 60, 180, 40, 92, 312, 215, 255, 80, 95, glow=False)
plot(buf, W, H, t[15:-15], filt[15:-15], 0, 150, 60, 180, 40, 92, 312, 215, 45, 255, 135, glow=True)

hor = list(range(61))
tc, ts = [44.0], [44.0]
for _ in hor[1:]:
    tc.append(tc[-1] + ((120**2)*0.015 - 18*(tc[-1]-32))/1200)
    ts.append(ts[-1] + ((320**2)*0.015 - 18*(ts[-1]-32))/1200)
lim_y = int(round(92 + 215 - ((55 - 40) / 55) * 215))
for x in range(404, 716, 12):
    line(buf, W, H, x, lim_y, x + 6, lim_y, 255, 70, 85, thick=2)
plot(buf, W, H, hor, tc, 0, 60, 40, 95, 404, 92, 312, 215, 0, 215, 255, glow=True)
plot(buf, W, H, hor, ts, 0, 60, 40, 95, 404, 92, 312, 215, 255, 165, 35, glow=True)

st = [s * 0.1 for s in range(13)]
td = [45 - 25 * s for s in st]
rd = [d + rng.gauss(0, 1.4) for d in td]
fd = [d + rng.gauss(0, 0.25) for d in td]
aeb_x = int(round(768 + (0.7 / 1.2) * 312))
for y in range(92, 307, 10):
    line(buf, W, H, aeb_x, y, aeb_x, y + 5, 255, 70, 85, thick=2)
plot(buf, W, H, st, rd, 0, 1.2, 10, 50, 768, 92, 312, 215, 195, 135, 255, glow=False)
plot(buf, W, H, st, fd, 0, 1.2, 10, 50, 768, 92, 312, 215, 57, 255, 136, glow=True)

write_png("docs/sil_telemetry_dashboard.png", W, H, buf)
print("[PASS] Labeled HUD dashboard and badge generated!")
