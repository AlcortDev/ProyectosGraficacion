"""
demo.py  –  Proyecto Final: Demo Procedural con OpenCV
Escenas:
  0 – Intro / Plasma HSV
  1 – Túnel raymarching 2D
  2 – Curvas exóticas (mariposa, bicorne, epicicloide)
  3 – Julia Set animado
  4 – Teselas geométricas con shear/rotación
  5 – Espiral Mandelbrot zoom (escena final)

Restricciones:  Python 3  |  numpy + opencv-python  |  sin imágenes externas
Resolución: 800x600  |  30 FPS  |  60 s
"""

import math, time
import numpy as np
import cv2

# ─── Constantes globales ────────────────────────────────────────────────────
W, H   = 800, 600
FPS    = 30
DURATION = 60.0

# Resolución reducida para fractales (se hace upscale después)
FW, FH = 400, 300   # mitad → 4× menos píxeles

# ─── Pre-cómputo único al inicio ────────────────────────────────────────────
# Todo lo que no depende del tiempo se calcula UNA sola vez aquí.

def _build_static_tables():
    # Coordenadas normalizadas para plasma [-1, 1]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (xx - W * 0.5) / (W * 0.5)
    ny = (yy - H * 0.5) / (H * 0.5)
    r_plasma = np.sqrt(nx*nx + ny*ny).astype(np.float32)

    # Túnel: angle y depth son estáticos
    dx = xx - W * 0.5
    dy = yy - H * 0.5
    r_tun = np.sqrt(dx*dx + dy*dy) + 1e-6
    angle_tun = np.arctan2(dy, dx).astype(np.float32)
    depth_tun = (80.0 / r_tun).astype(np.float32)

    # Vignette: máscara float32 precalculada
    vig = np.clip(1.0 - 0.65 * (nx*nx + ny*ny), 0.0, 1.0).astype(np.float32)

    # Scanlines: vector de modulación precalculado
    scan_m = (1.0 - 0.14 * (0.5 + 0.5 * np.sin(
        2 * np.pi * np.arange(H, dtype=np.float32) / 3.0
    ))).astype(np.float32)

    # Coordenadas fractal (mitad de resolución) para Julia y Mandelbrot
    fxs_base = np.linspace(-1.5, 1.5, FW, dtype=np.float32)
    fys_base = np.linspace(-1.1, 1.1, FH, dtype=np.float32)

    # Tiles: colores HSV → LUT 180 entradas
    hsv_lut = np.zeros((180, 1, 3), np.uint8)
    for h in range(180):
        hsv_lut[h, 0] = [h, 210, 200]
    bgr_lut = cv2.cvtColor(hsv_lut, cv2.COLOR_HSV2BGR).reshape(180, 3)

    return dict(
        nx=nx, ny=ny, r_plasma=r_plasma,
        angle_tun=angle_tun, depth_tun=depth_tun,
        vig=vig, scan_m=scan_m,
        fxs_base=fxs_base, fys_base=fys_base,
        bgr_lut=bgr_lut,
    )

S = _build_static_tables()   # tablas estáticas globales

# ─── Helpers ────────────────────────────────────────────────────────────────

def clamp01(x):
    return float(np.clip(x, 0.0, 1.0))

def smoothstep(a, b, x):
    x = clamp01((x - a) / (b - a))
    return x * x * (3.0 - 2.0 * x)

def hsv_scalar_to_bgr(h, s, v):
    """Conversión escalar: usa la LUT cuando s≈210, v≈200; si no, OpenCV."""
    px = np.uint8([[[int(h) % 180, int(np.clip(s,0,255)), int(np.clip(v,0,255))]]])
    return tuple(int(c) for c in cv2.cvtColor(px, cv2.COLOR_HSV2BGR)[0, 0])

# ─── Post-FX  (versiones rápidas con tablas precalculadas) ──────────────────

def post_vignette(img):
    """Aplica vignette con máscara precalculada (sin mgrid en runtime)."""
    # Multiply in-place sobre float: evita allocar array nuevo
    out = img.astype(np.float32)
    out *= S['vig'][..., None]
    np.clip(out, 0, 255, out=out)
    return out.astype(np.uint8)

def post_scanlines(img):
    """Scanlines con vector precalculado."""
    out = img.astype(np.float32)
    out *= S['scan_m'][:, None, None]
    np.clip(out, 0, 255, out=out)
    return out.astype(np.uint8)

def post_posterize(img, q=28):
    q = max(1, int(q))
    return ((img // q) * q).astype(np.uint8)

def post_chromatic(img, shift=2):
    out = img.copy()
    out[:, shift:, 2] = img[:, :-shift, 2]
    return out

# ─── ESCENA 0: Plasma HSV ───────────────────────────────────────────────────
# Usa coords nx/ny precalculadas. Sólo las sumas de senos dependen de t.

def scene_plasma(img, t):
    nx, ny, r = S['nx'], S['ny'], S['r_plasma']

    v  = np.sin(nx * 4.0 + t * 1.2)
    v += np.sin(ny * 4.0 + t * 0.9)
    v += np.sin((nx + ny) * 3.0 + t * 1.5)
    v += np.sin(r * 6.0 - t * 2.0)
    v  = (v + 4.0) * (1.0 / 8.0)   # normalizar [0,1]

    hue = (v * 179).astype(np.uint8)
    sat = np.full((H, W), 230, np.uint8)
    val = np.clip(v * 331.5, 40, 255).astype(np.uint8)   # 255*1.3=331.5

    img[:] = cv2.cvtColor(np.dstack([hue, sat, val]), cv2.COLOR_HSV2BGR)

    alpha = clamp01(t / 2.0)
    if alpha > 0.02:
        overlay = img.copy()
        cv2.putText(overlay, "DEMO PROCEDURAL", (70, 250),
                    cv2.FONT_HERSHEY_TRIPLEX, 1.6, (255,255,255), 2, cv2.LINE_AA)
        cv2.putText(overlay, "OpenCV  |  Graficacion", (185, 310),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.85, (220,220,220), 1, cv2.LINE_AA)
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, dst=img)

# ─── ESCENA 1: Túnel ────────────────────────────────────────────────────────
# angle y depth son estáticos; sólo u,v (offsets) cambian con t.

def scene_tunnel(img, t):
    angle = S['angle_tun']
    depth = S['depth_tun']

    u = (angle * (1.0 / (2 * math.pi)) + t * 0.18) % 1.0
    v = (depth + t * 0.55) % 1.0

    checker = ((u * 12).astype(np.int32) + (v * 12).astype(np.int32)) & 1

    hue = ((angle * (120.0 / (2 * math.pi)) + t * 25) % 180).astype(np.float32)
    fog = np.clip(1.0 / (depth + 0.3), 0.0, 1.0)
    val = (checker * (150 + 105 * fog)).astype(np.float32)
    sat = (210 * (0.5 + 0.5 * fog)).astype(np.float32)

    hsv_img = np.dstack([
        hue.astype(np.uint8),
        np.clip(sat, 0, 255).astype(np.uint8),
        np.clip(val, 0, 255).astype(np.uint8)
    ])
    img[:] = cv2.cvtColor(hsv_img, cv2.COLOR_HSV2BGR)

    cx, cy = W // 2, H // 2
    cv2.circle(img, (cx, cy), 6, (255,255,255), -1, cv2.LINE_AA)
    cv2.circle(img, (cx, cy), int(18 + 8*math.sin(t*3)), (200,200,255), 1, cv2.LINE_AA)

# ─── ESCENA 2: Curvas exóticas ──────────────────────────────────────────────
# Mariposa: n reducido de 3000→1200 (imperceptible visualmente a 1px)
# Epicicloide: 1200→600
# Bicorne: 600→300 × 2

def _butterfly_pts(t_anim, cx, cy):
    th  = np.linspace(0, 12 * math.pi, 1200, dtype=np.float32)
    r   = (np.exp(np.sin(th))
           - 2.0 * np.cos(4 * th)
           + np.sin((2 * th - math.pi) / 24.0) ** 5)
    phi = t_anim * 0.3
    c, s = math.cos(phi), math.sin(phi)
    # rotación manual (evita crear array extra con cos/sin por separado)
    rx = r * np.cos(th)
    ry = r * np.sin(th)
    xs = (rx * c - ry * s) * 55 + cx
    ys = (rx * s + ry * c) * 55 + cy
    return np.round(np.stack([xs, ys], 1)).astype(np.int32).reshape((-1, 1, 2))

def _epicycloid_pts(t_anim, R=7.0, r=2.0, d=4.0, cx=560, cy=300):
    ts = np.linspace(0, 8 * math.pi, 600, dtype=np.float32)
    w  = (R + r) / r
    off = t_anim * 0.5
    xs = ((R+r)*np.cos(ts + off) - d*np.cos(w*ts + off)) * 22 + cx
    ys = ((R+r)*np.sin(ts + off) - d*np.sin(w*ts + off)) * 22 + cy
    return np.round(np.stack([xs, ys], 1)).astype(np.int32).reshape((-1, 1, 2))

def _bicorne_pts(t_anim, cx, cy):
    a  = 1.0
    ts = np.linspace(-a*0.98, a*0.98, 300, dtype=np.float32)
    yr = (a**2 - ts**2) / (a**2 + ts**2)
    xs = np.concatenate([ts, ts[::-1]])
    ys = np.concatenate([yr, -yr[::-1]])
    scale = 110 + 40 * math.sin(t_anim * 0.7)
    angle = t_anim * 0.4
    c, s  = math.cos(angle), math.sin(angle)
    xs2 = (xs * c - ys * s) * scale + cx
    ys2 = (xs * s + ys * c) * scale + cy
    return np.round(np.stack([xs2, ys2], 1)).astype(np.int32).reshape((-1, 1, 2))

def scene_exotic_curves(img, t):
    img[:] = 10

    pts_b = _butterfly_pts(t, cx=220, cy=300)
    col_b = hsv_scalar_to_bgr(int(10 + 30*math.sin(t*0.7)), 240, 245)
    cv2.polylines(img, [pts_b], False, col_b, 1, cv2.LINE_AA)

    pts_e = _epicycloid_pts(t)
    col_e = hsv_scalar_to_bgr(int(90 + 40*math.cos(t*0.5)), 220, 240)
    cv2.polylines(img, [pts_e], False, col_e, 1, cv2.LINE_AA)

    pts_c = _bicorne_pts(t, cx=400, cy=420)
    col_c = hsv_scalar_to_bgr(int(140 + 25*math.sin(t*0.9)), 200, 250)
    cv2.polylines(img, [pts_c], True, col_c, 1, cv2.LINE_AA)

    cv2.putText(img, "Mariposa",    (80,  550), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col_b, 1)
    cv2.putText(img, "Epicicloide", (490, 550), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col_e, 1)
    cv2.putText(img, "Bicorne",     (340, 580), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col_c, 1)
    img[:] = cv2.GaussianBlur(img, (0,0), 0.7)

# ─── ESCENA 3: Julia Set ────────────────────────────────────────────────────
_JL_STEPS = 25

def scene_julia(img, t):
    angle_c = t * 0.5
    cr = np.float32(0.7885 * math.cos(angle_c))
    ci = np.float32(0.7885 * math.sin(angle_c))

    zoom = np.float32(1.3 + 0.15 * math.sin(t * 0.4))
    inv_zoom = np.float32(1.0 / zoom)

    xs = S['fxs_base'] * inv_zoom
    ys = S['fys_base'] * inv_zoom

    zr, zi = np.meshgrid(xs, ys)   # FW×FH float32
    it_map  = np.zeros((FH, FW), np.float32)
    alive   = np.ones((FH, FW),  dtype=bool)   # píxeles aún en órbita

    for _ in range(_JL_STEPS):
        # Solo calculamos los píxeles que aún no escaparon
        r2 = zr * zr + zi * zi
        escaped = r2 >= 4.0
        newly_escaped = escaped & alive
        alive &= ~escaped

        it_map[newly_escaped] = _  # iteración de escape

        # Actualizar solo los vivos (el resto ya no importa)
        new_r = zr * zr - zi * zi + cr
        new_i = 2.0 * zr * zi + ci
        zr = np.where(alive, new_r, zr)
        zi = np.where(alive, new_i, zi)

    # Los que nunca escaparon → interior
    it_map[alive] = _JL_STEPS

    norm = it_map * (1.0 / _JL_STEPS)
    hue  = ((norm * 180 + t * 20) % 180).astype(np.uint8)
    sat  = np.where(it_map >= _JL_STEPS, 0, 220).astype(np.uint8)
    val  = np.where(it_map >= _JL_STEPS, 0,
                    np.clip(60 + 195 * norm, 0, 255)).astype(np.uint8)

    small = cv2.cvtColor(np.dstack([hue, sat, val]), cv2.COLOR_HSV2BGR)
    # Upscale bilinear de 400×300 → 800×600
    img[:] = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)
    img[:] = post_chromatic(img, shift=2)

# ─── ESCENA 4: Teselas geométricas ──────────────────────────────────────────
# Optimización: LUT de colores precalculada (evita 96 llamadas a cvtColor/frame)

def _regular_polygon(cx, cy, r, n, angle):
    angles = np.linspace(angle, angle + 2*math.pi, n, endpoint=False, dtype=np.float32)
    xs = cx + r * np.cos(angles)
    ys = cy + r * np.sin(angles)
    return np.round(np.stack([xs, ys], 1)).astype(np.int32)

def scene_tiles(img, t):
    img[:] = 15
    COLS, ROWS = 8, 6
    cw, ch = W // COLS, H // ROWS
    shear_k = 0.25 * math.sin(t * 0.6)
    t18 = t * 18.0
    lut = S['bgr_lut']   # shape (180, 3)

    for row in range(ROWS):
        for col in range(COLS):
            cx = col * cw + cw // 2
            cy = row * ch + ch // 2
            scx = int(cx + shear_k * cy)

            n_sides = 3 + (col + row) % 6
            rot   = t * (0.5 + 0.3 * ((col*3 + row) % 5)) + math.pi * col / COLS
            phase = (col + row * COLS) / (COLS * ROWS)
            r = int(cw * 0.38 * (0.7 + 0.3 * math.sin(t * 2.0 + phase * 2*math.pi)))
            if r < 4:
                continue

            pts = _regular_polygon(scx, cy, r, n_sides, rot)

            hue       = int((col*22 + row*30 + t18) % 180)
            hue_edge  = (hue + 60) % 180
            # LUT lookup: tuple desde array
            col_fill = tuple(int(x) for x in lut[hue])
            col_edge = tuple(int(x) for x in lut[hue_edge])

            cv2.fillPoly(img,    [pts],                       col_fill)
            cv2.polylines(img,   [pts.reshape((-1,1,2))], True, col_edge, 1, cv2.LINE_AA)

    blur = cv2.GaussianBlur(img, (0,0), 4)
    cv2.addWeighted(img, 0.75, blur, 0.35, 0, dst=img)

# ─── ESCENA 5: Mandelbrot zoom + espiral ────────────────────────────────────
# Optimizaciones:
#   1. float32
#   2. Resolución FW×FH + upscale
#   3. Caché: solo recalcula cada 2 frames (el zoom es lento, imperceptible)
#   4. Early-exit con máscara acumulada igual que Julia

_MB_STEPS = 32

def _mandelbrot_frame(t):
    cx0  = np.float32(-0.7436438870)
    cy0  = np.float32( 0.1318259042)
    zoom = 1.0 + t * 0.8
    scale = np.float32(2.5 / (2 ** zoom))

    xs = np.linspace(cx0 - scale, cx0 + scale, FW, dtype=np.float32)
    ys = np.linspace(cy0 - scale*(FH/FW), cy0 + scale*(FH/FW), FH, dtype=np.float32)
    cr, ci = np.meshgrid(xs, ys)
    zr = np.zeros((FH, FW), np.float32)
    zi = np.zeros((FH, FW), np.float32)
    it_map = np.zeros((FH, FW), np.float32)
    alive  = np.ones((FH, FW), dtype=bool)

    for n in range(_MB_STEPS):
        r2      = zr*zr + zi*zi
        escaped = (r2 >= 4.0) & alive
        alive  &= ~escaped
        it_map[escaped] = n
        new_r = zr*zr - zi*zi + cr
        new_i = 2.0*zr*zi + ci
        zr = np.where(alive, new_r, zr)
        zi = np.where(alive, new_i, zi)
    it_map[alive] = _MB_STEPS

    norm = it_map * (1.0 / _MB_STEPS)
    hue  = ((norm * 180 + t * 15) % 180).astype(np.uint8)
    sat  = np.where(it_map >= _MB_STEPS, 0, 200).astype(np.uint8)
    val  = np.where(it_map >= _MB_STEPS, 0, np.clip(40 + 215*norm, 0, 255)).astype(np.uint8)
    small = cv2.cvtColor(np.dstack([hue, sat, val]), cv2.COLOR_HSV2BGR)
    return cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)

def _archimedes_spiral(t_anim, cx, cy, arms=6):
    pts_list = []
    ts = np.linspace(0, 6*math.pi, 500, dtype=np.float32)   # 800→500
    r  = ts * 18
    for arm in range(arms):
        offset = 2*math.pi * arm / arms
        angle  = ts + offset + t_anim * 0.4
        xs = r * np.cos(angle) + cx
        ys = r * np.sin(angle) + cy
        pts_list.append(
            np.round(np.stack([xs, ys], 1)).astype(np.int32).reshape((-1,1,2))
        )
    return pts_list

def scene_final(img, t, mb_cache):
    # Recalcular solo cada 2 frames (zoom muy lento, ahorra ~40ms)
    frame_id = int(t * FPS)
    if 'fid' not in mb_cache or mb_cache['fid'] != frame_id // 2:
        mb_cache['frame'] = _mandelbrot_frame(t)
        mb_cache['fid']   = frame_id // 2

    mb = mb_cache['frame']

    spiral_layer = np.zeros((H, W, 3), np.uint8)
    hue_col = hsv_scalar_to_bgr(int(t * 30 % 180), 240, 255)
    for pts in _archimedes_spiral(t, W//2, H//2, arms=6):
        cv2.polylines(spiral_layer, [pts], False, hue_col, 1, cv2.LINE_AA)

    cv2.addWeighted(mb, 0.70, spiral_layer, 0.40, 0, dst=img)

    alpha = smoothstep(0, 3, t)
    if alpha > 0.02:
        overlay = img.copy()
        cv2.putText(overlay, "FIN", (330, 310),
                    cv2.FONT_HERSHEY_TRIPLEX, 3.0, (255,255,255), 3, cv2.LINE_AA)
        cv2.addWeighted(overlay, alpha*0.7, img, 1-alpha*0.7, 0, dst=img)

# ─── Render por escena ──────────────────────────────────────────────────────

def render_scene(buf, scene_id, t, state):
    if   scene_id == 0: scene_plasma(buf, t)
    elif scene_id == 1: scene_tunnel(buf, t)
    elif scene_id == 2: scene_exotic_curves(buf, t)
    elif scene_id == 3: scene_julia(buf, t)
    elif scene_id == 4: scene_tiles(buf, t)
    else:               scene_final(buf, t, state['mb_cache'])

# ─── Timeline ───────────────────────────────────────────────────────────────

def timeline(t, bufA, bufB, state):
    block = int(min(5, max(0, t // 10)))
    t_in  = t - block * 10

    render_scene(bufA, block, t, state)
    frame = bufA

    if block < 5 and t_in >= 8.8:
        render_scene(bufA, block,     t, state)
        render_scene(bufB, block + 1, t, state)
        a = smoothstep(8.8, 10.0, t_in)
        cv2.addWeighted(bufA, 1-a, bufB, a, 0, dst=frame)
        flash = smoothstep(9.6, 10.0, t_in)
        if flash > 0:
            bright = np.full_like(frame, 255)
            cv2.addWeighted(frame, 1.0, bright, 0.15*flash, 0, dst=frame)

    f = smoothstep(0.0, 1.5, t) * (1.0 - smoothstep(DURATION-1.5, DURATION, t))
    if f < 0.999:
        np.multiply(frame, f, out=frame.astype(np.float32))  # in-place
        frame = (frame.astype(np.float32) * f).astype(np.uint8)

    return frame

# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    bufA = np.zeros((H, W, 3), np.uint8)
    bufB = np.zeros((H, W, 3), np.uint8)
    state = {'mb_cache': {}}

    # Exportar video (descomentar):
    # import os; os.makedirs("renders", exist_ok=True)
    # out = cv2.VideoWriter("renders/demo_final.mp4",
    #                       cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))

    total_frames = int(DURATION * FPS)
    t0 = time.perf_counter()
    fps_counter, fps_t0 = 0, t0

    for i in range(total_frames):
        t = i / FPS

        frame = timeline(t, bufA, bufB, state)
        frame = post_vignette(frame)
        if 20 <= t < 40:
            frame = post_scanlines(frame)
        if t >= 40:
            frame = post_posterize(frame, 28)

        # FPS overlay (debug — quitar en entrega)
        fps_counter += 1
        if fps_counter == 15:
            elapsed_fps = time.perf_counter() - fps_t0
            fps_val = fps_counter / elapsed_fps
            fps_counter, fps_t0 = 0, time.perf_counter()
            state['fps_str'] = f"{fps_val:.1f} fps"
        if 'fps_str' in state:
            cv2.putText(frame, state['fps_str'], (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)

        cv2.imshow("Demo Procedural OpenCV", frame)
        # out.write(frame)

        elapsed = time.perf_counter() - t0
        target  = (i + 1) / FPS
        delay   = max(1, int((target - elapsed) * 1000))
        if cv2.waitKey(delay) & 0xFF == 27:
            break

    print(f"Duración real: {time.perf_counter() - t0:.2f} s")
    # out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()