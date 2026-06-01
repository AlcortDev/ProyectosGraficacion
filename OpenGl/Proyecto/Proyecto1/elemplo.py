import time, math
import numpy as np
import cv2

W, H = 800, 600
FPS = 30
DURATION = 60.0

def clamp01(x): return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)
def smoothstep(a, b, x):
    x = clamp01((x - a) / (b - a))
    return x * x * (3 - 2 * x)

def poly_param(fx, fy, t0, t1, n, cx, cy, sx, sy):
    ts = np.linspace(t0, t1, n, dtype=np.float32)
    xs = fx(ts) * sx + cx
    ys = fy(ts) * sy + cy
    return np.round(np.stack([xs, ys], 1)).astype(np.int32).reshape((-1, 1, 2))

def hsv_to_bgr(h, s, v):
    # OpenCV: H en [0,179], S,V en [0,255]
    hsv = np.uint8([[[h % 180, np.clip(s, 0, 255), np.clip(v, 0, 255)]]])
    return tuple(int(x) for x in cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0, 0])

def post_vignette(img, strength=0.7):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (xx - W*0.5) / (W*0.5)
    ny = (yy - H*0.5) / (H*0.5)
    r2 = nx*nx + ny*ny
    mask = np.clip(1.0 - strength * r2, 0.0, 1.0)
    out = (img.astype(np.float32) * mask[..., None]).astype(np.uint8)
    return out

def post_scanlines(img, strength=0.22):
    out = img.astype(np.float32)
    y = np.arange(H, dtype=np.float32)
    m = 1.0 - strength * (0.5 + 0.5*np.sin(2*np.pi*y/3.0))
    out *= m[:, None, None]
    return np.clip(out, 0, 255).astype(np.uint8)

def post_posterize(img, q=32):
    q = max(1, int(q))
    return ((img // q) * q).astype(np.uint8)

def background_hsv_gradient(img, t, hue0=10, hue1=140):
    # Degradado vertical en HSV para cambiar “ambiente” por escena
    hsv = np.zeros((H, W, 3), np.uint8)
    ys = np.linspace(0, 1, H, dtype=np.float32)
    hue = (hue0 + (hue1 - hue0) * ys + 10*np.sin(t*0.4 + ys*2.0)).astype(np.float32)
    hsv[:, :, 0] = np.clip(hue, 0, 179).astype(np.uint8)[:, None]
    hsv[:, :, 1] = 200
    hsv[:, :, 2] = (40 + 120*(1 - ys)).astype(np.uint8)[:, None]
    img[:] = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

def scene_credits(img, t):
    background_hsv_gradient(img, t, hue0=165, hue1=105)
    # “estrellas” deterministas
    rng = np.random.default_rng(1)
    xs = rng.integers(0, W, 380)
    ys = rng.integers(0, int(H*0.65), 380)
    img[ys, xs] = (255, 255, 255)
    img[:] = cv2.GaussianBlur(img, (0,0), 0.6)
    cv2.putText(img, "DEMO PROCEDURAL (GRAFICACION)", (42, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.95, (245,245,245), 2, cv2.LINE_AA)
    cv2.putText(img, "OpenCV + Matematicas", (42, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (220,220,220), 2, cv2.LINE_AA)

def scene_lissajous(img, t):
    background_hsv_gradient(img, t, hue0=18, hue1=60)
    a = 3 + 0.7 * math.sin(t*0.6)
    b = 2 + 0.7 * math.cos(t*0.8)
    delta = math.pi/2 + 0.4*math.sin(t*0.3)
    fx = lambda x: np.sin(a*x + delta)
    fy = lambda x: np.sin(b*x)
    pts = poly_param(fx, fy, 0, 2*math.pi, 900, W*0.5, H*0.45, 260, 180)
    col = hsv_to_bgr(int(20 + 30*np.sin(t*0.8)), 210, 240)
    cv2.polylines(img, [pts], False, col, 2, cv2.LINE_AA)

def scene_rose_polar(img, t):
    background_hsv_gradient(img, t, hue0=120, hue1=165)
    # Rosa polar: r = cos(k*theta)
    k = 5
    theta0 = t * 0.6
    fx = lambda th: np.cos(k*th) * np.cos(th + theta0)
    fy = lambda th: np.cos(k*th) * np.sin(th + theta0)
    pts = poly_param(fx, fy, 0, 2*math.pi, 1200, W*0.5, H*0.45, 240, 240)
    col = hsv_to_bgr(int(145 + 25*np.sin(t*0.5)), 220, 245)
    cv2.polylines(img, [pts], False, col, 2, cv2.LINE_AA)
    # Círculos “beats”
    for i in range(6):
        r = int(18 + 10*np.sin(t*2.0 + i))
        cv2.circle(img, (int(W*0.18 + i*110), int(H*0.78)), max(1, r), (230,230,230), 1, cv2.LINE_AA)

def scene_spirograph(img, t):
    background_hsv_gradient(img, t, hue0=80, hue1=20)
    # Hipotrocoide (spirograph): (R-r)cos(t) + d cos((R-r)/r * t)
    R, r, d = 8.0, 3.0, 5.0
    w = (R - r) / r
    fx = lambda x: (R-r)*np.cos(x) + d*np.cos(w*x + 0.4*np.sin(t*0.7))
    fy = lambda x: (R-r)*np.sin(x) - d*np.sin(w*x + 0.4*np.cos(t*0.6))
    pts = poly_param(fx, fy, 0, 14*math.pi, 1600, W*0.5, H*0.46, 26, 26)
    col = hsv_to_bgr(int(10 + 140*(0.5+0.5*np.sin(t*0.4))), 240, 240)
    cv2.polylines(img, [pts], False, col, 2, cv2.LINE_AA)
    img[:] = post_scanlines(img, 0.18)

def scene_particles(img, t, rng):
    background_hsv_gradient(img, t, hue0=150, hue1=100)
    n = 1200
    xs = rng.random(n) * W
    ys = rng.random(n) * H
    xs = (xs + 110*np.sin(ys/55.0 + t*1.7) + 40*np.cos(t*0.7)) % W
    ys = (ys + 85*np.cos(xs/75.0 + t*1.2) + 30*np.sin(t*0.9)) % H
    # “brillo” por velocidad (fake)
    v = (0.5 + 0.5*np.sin(t*1.9)).astype(float) if hasattr(t, "astype") else (0.5 + 0.5*math.sin(t*1.9))
    col = hsv_to_bgr(int(95 + 40*math.sin(t*0.8)), 210, int(210 + 40*v))
    img[ys.astype(np.int32), xs.astype(np.int32)] = col
    img[:] = cv2.GaussianBlur(img, (0,0), 1.1)

def scene_fire(img, t, state):
    # “Fuego” procedural: partículas + heatmap + paleta HSV
    heat = state["heat"]
    rng = state["rng"]
    heat[:] = (heat * 0.93).astype(np.float32)

    # Inyección en la base (más calor = más fuego)
    base_n = 1400
    xs = rng.integers(0, W, base_n)
    ys = rng.integers(int(H*0.82), H, base_n)
    heat[ys, xs] += rng.random(base_n) * (0.8 + 0.6*(0.5+0.5*math.sin(t*2.0)))

    # “subida” del calor: blur anisotrópico + desplazamiento hacia arriba
    heat[:] = cv2.GaussianBlur(heat, (0, 0), 2.2)
    heat[:-2, :] = heat[2:, :]  # desplaza hacia arriba (convección barata)
    heat[-2:, :] *= 0.0

    # Mapeo a color con HSV (rojo->amarillo->blanco)
    h = (20 - 20*np.clip(heat, 0, 1)).astype(np.uint8)      # 20..0
    s = (220 - 80*np.clip(heat, 0, 1)).astype(np.uint8)     # 220..140
    v = (60 + 195*np.clip(heat, 0, 1)).astype(np.uint8)     # 60..255
    hsv = np.dstack([h, s, v]).astype(np.uint8)
    img[:] = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    # Silueta y chispas
    cv2.rectangle(img, (0, int(H*0.83)), (W, H), (10, 10, 10), -1)
    sparks = 160
    sx = rng.integers(0, W, sparks)
    sy = rng.integers(int(H*0.55), int(H*0.9), sparks)
    img[sy, sx] = (255, 255, 255)
    img[:] = cv2.GaussianBlur(img, (0,0), 0.6)

def render_scene(buf, scene_id, t, rng, fire_state):
    if scene_id == 0:
        scene_credits(buf, t)
    elif scene_id == 1:
        scene_lissajous(buf, t)
    elif scene_id == 2:
        scene_rose_polar(buf, t)
    elif scene_id == 3:
        scene_spirograph(buf, t)
    elif scene_id == 4:
        scene_particles(buf, t, rng)
    else:
        scene_fire(buf, t, fire_state)

def timeline(t, rng, bufA, bufB, fire_state):
    # 6 escenas (0..5) con 5 transiciones entre ellas
    # Duración 60s -> 6 bloques de 10s
    block = int(min(5, max(0, t // 10)))
    t_in = t - block*10

    # Render escena base
    render_scene(bufA, block, t, rng, fire_state)
    frame = bufA

    # 5 transiciones: de s a s+1 en los últimos 1.2s de cada bloque
    if block < 5 and t_in >= 8.8:
        render_scene(bufA, block, t, rng, fire_state)
        render_scene(bufB, block+1, t, rng, fire_state)
        a = smoothstep(8.8, 10.0, t_in)
        frame = cv2.addWeighted(bufA, 1-a, bufB, a, 0)
        # pequeño “flash” al final de transición
        flash = smoothstep(9.6, 10.0, t_in)
        if flash > 0:
            frame = cv2.addWeighted(frame, 1.0, np.full_like(frame, 255), 0.12*flash, 0)

    # Fade in/out global
    fin = smoothstep(0.0, 1.5, t)
    fout = 1.0 - smoothstep(DURATION - 1.5, DURATION, t)
    f = fin * fout
    if f < 0.999:
        frame = (frame.astype(np.float32) * f).astype(np.uint8)
    return frame

def main():
    rng = np.random.default_rng(123)
    bufA = np.zeros((H, W, 3), np.uint8)
    bufB = np.zeros((H, W, 3), np.uint8)

    fire_state = {
        "heat": np.zeros((H, W), np.float32),
        "rng": np.random.default_rng(999),
    }

    total_frames = int(DURATION * FPS)
    t0 = time.perf_counter()
    for i in range(total_frames):
        t = i / FPS
        frame = timeline(t, rng, bufA, bufB, fire_state)
        frame = post_vignette(frame, 0.72)
        frame = post_scanlines(frame, 0.16)
        frame = post_posterize(frame, 24)
        cv2.imshow("Proyecto Final: demo procedural (OpenCV)", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
    print("Tiempo:", time.perf_counter() - t0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()