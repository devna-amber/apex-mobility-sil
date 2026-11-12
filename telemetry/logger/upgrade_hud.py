import math, random, struct, zlib

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
        p0, p1 = pts[i-1], pts[i]
        if glow:
            line(buf, w, h, p0[0], p0[1], p1[0], p1[1], r, g, b, thick=7, a=0.16)
        line(buf, w, h, p0[0], p0[1], p1[0], p1[1], r, g, b, thick=2 if glow else 1, a=1.0 if glow else 0.7)

W, H = 1120, 320
buf = bytearray(bytes((9, 13, 22)) * (W * H))
for cx in (22, 386, 750):
    for y in range(22, 298):
        for x in range(cx, cx + 348):
            px(buf, W, H, x, y, 15, 22, 34)
    line(buf, W, H, cx, 22, cx + 347, 22, 0, 220, 255, thick=2)
    line(buf, W, H, cx, 297, cx + 347, 297, 35, 55, 78, thick=1)
    for gx in range(cx + 18, cx + 335, 35):
        for y in range(36, 284, 5):
            px(buf, W, H, gx, y, 32, 45, 62)
    for gy in range(36, 285, 35):
        for x in range(cx + 18, cx + 334, 5):
            px(buf, W, H, x, gy, 32, 45, 62)

rng = random.Random(42)
t = [i * 0.5 for i in range(300)]
clean = [120 + 35 * math.sin(2 * math.pi * 5 * (i / 2000)) for i in range(300)]
noisy = [clean[i] + 18 * math.sin(2 * math.pi * 450 * (i / 2000)) + rng.gauss(0, 2.2) for i in range(300)]
filt = [sum(noisy[max(0, min(299, i - k + 12))] for k in range(25)) / 25.0 for i in range(300)]
plot(buf, W, H, t[15:-15], noisy[15:-15], 0, 150, 60, 180, 40, 38, 312, 244, 255, 80, 95, glow=False)
plot(buf, W, H, t[15:-15], filt[15:-15], 0, 150, 60, 180, 40, 38, 312, 244, 45, 255, 135, glow=True)

hor = list(range(61))
tc, ts = [44.0], [44.0]
for _ in hor[1:]:
    tc.append(tc[-1] + ((120**2)*0.015 - 18*(tc[-1]-32))/1200)
    ts.append(ts[-1] + ((320**2)*0.015 - 18*(ts[-1]-32))/1200)
lim_y = int(round(38 + 244 - ((55 - 40) / 55) * 244))
for x in range(404, 716, 12):
    line(buf, W, H, x, lim_y, x + 6, lim_y, 255, 70, 85, thick=2)
plot(buf, W, H, hor, tc, 0, 60, 40, 95, 404, 38, 312, 244, 0, 215, 255, glow=True)
plot(buf, W, H, hor, ts, 0, 60, 40, 95, 404, 38, 312, 244, 255, 165, 35, glow=True)

st = [s * 0.1 for s in range(13)]
td = [45 - 25 * s for s in st]
rd = [d + rng.gauss(0, 1.4) for d in td]
fd = [d + rng.gauss(0, 0.25) for d in td]
aeb_x = int(round(768 + (0.7 / 1.2) * 312))
for y in range(38, 282, 10):
    line(buf, W, H, aeb_x, y, aeb_x, y + 5, 255, 70, 85, thick=2)
plot(buf, W, H, st, rd, 0, 1.2, 10, 50, 768, 38, 312, 244, 195, 135, 255, glow=False)
plot(buf, W, H, st, fd, 0, 1.2, 10, 50, 768, 38, 312, 244, 57, 255, 136, glow=True)

write_png("docs/sil_telemetry_dashboard.png", W, H, buf)
print("[PASS] Glowing HUD dashboard generated!")
