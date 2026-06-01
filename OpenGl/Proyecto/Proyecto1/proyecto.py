"""
demo.py — Demo Procedural con OpenCV
=====================================
Proyecto Final de Graficación.
Todo lo visual se genera proceduralmente (sin imágenes externas).

Resolución : 800 × 600 px
FPS objetivo: 30
Duración    : 60 segundos
Escenas     : 6 (cada una dura 10 s con fade de 1.2 s entre ellas)

Dependencias: numpy, opencv-python
Ejecución   : python demo.py
Exportar MP4: python demo.py --export
"""



import math
import time
import argparse

import numpy as np
import cv2

# ─────────────────────────────────────────────
# CONSTANTES GLOBALES
# ─────────────────────────────────────────────
W        = 800          # ancho del frame en píxeles
H        = 600          # alto del frame en píxeles
FPS      = 30           # cuadros por segundo objetivo
DURATION = 60.0         # duración total del demo en segundos


# ─────────────────────────────────────────────
# UTILIDADES MATEMÁTICAS
# ─────────────────────────────────────────────

def clamp01(x):
    """Recorta un valor flotante al rango [0, 1]."""
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def smoothstep(a, b, x):
    """
    Interpolación suave de Hermite entre a y b.
    Devuelve 0 cuando x ≤ a, 1 cuando x ≥ b,
    y una curva S en el intervalo (a, b).
    Fórmula: 3t² − 2t³  donde t = (x−a)/(b−a)
    """
    x = clamp01((x - a) / (b - a))
    return x * x * (3 - 2 * x)


# ─────────────────────────────────────────────
# CONSTRUCCIÓN DE CURVAS PARAMÉTRICAS
# ─────────────────────────────────────────────

def poly_param(fx, fy, t0, t1, n, cx, cy, sx, sy):
    """
    Muestrea dos funciones paramétricas fx(t) y fy(t) en 'n' puntos
    dentro del intervalo [t0, t1] y devuelve un array de puntos enteros
    con el formato que espera cv2.polylines.

    Parámetros
    ----------
    fx, fy : callable   — funciones que aceptan arrays numpy
    t0, t1 : float      — rango del parámetro
    n      : int        — número de muestras
    cx, cy : float      — traslación del centro de la curva
    sx, sy : float      — escala (amplitud) en x e y
    """
    ts = np.linspace(t0, t1, n, dtype=np.float32)   # muestras del parámetro
    xs = fx(ts) * sx + cx                            # coordenadas x trasladadas
    ys = fy(ts) * sy + cy                            # coordenadas y trasladadas
    # cv2.polylines necesita shape (N, 1, 2) con dtype int32
    return np.round(np.stack([xs, ys], axis=1)).astype(np.int32).reshape((-1, 1, 2))


# ─────────────────────────────────────────────
# CONVERSIÓN DE COLOR HSV → BGR
# ─────────────────────────────────────────────

def hsv_to_bgr(h, s, v):
    """
    Convierte un color HSV escalar a BGR (tuple de ints).
    OpenCV usa: H ∈ [0, 179], S y V ∈ [0, 255].
    """
    hsv = np.uint8([[[h % 180, np.clip(s, 0, 255), np.clip(v, 0, 255)]]])
    return tuple(int(x) for x in cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0, 0])


# ─────────────────────────────────────────────
# POST-EFECTOS (FILTROS)
# ─────────────────────────────────────────────

def post_vignette(img, strength=0.7):
    """
    TRANSFORMACIÓN — Composición por capas (multiplicación por máscara).
    Oscurece los bordes del frame simulando el viñeteo de una lente.

    Se genera una máscara radial 1 − strength·r² y se multiplica
    canal a canal sobre la imagen (addWeighted implícito vía producto).
    """
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # Coordenadas normalizadas centradas en (0,0), rango ≈ [-1, 1]
    nx = (xx - W * 0.5) / (W * 0.5)
    ny = (yy - H * 0.5) / (H * 0.5)
    r2 = nx * nx + ny * ny                              # distancia² al centro
    mask = np.clip(1.0 - strength * r2, 0.0, 1.0)      # máscara circular
    out = (img.astype(np.float32) * mask[..., None]).astype(np.uint8)
    return out


def post_scanlines(img, strength=0.22):
    """
    POST-EFECTO — Scanlines de CRT (líneas horizontales semitransparentes).
    Modula el brillo con una senoidal de período 3 px para imitar
    la pantalla de tubo de rayos catódicos de los demos retro.
    """
    out = img.astype(np.float32)
    y   = np.arange(H, dtype=np.float32)
    # Modulación: valores entre (1−strength) y 1
    m   = 1.0 - strength * (0.5 + 0.5 * np.sin(2 * np.pi * y / 3.0))
    out *= m[:, None, None]                              # broadcast a los 3 canales
    return np.clip(out, 0, 255).astype(np.uint8)


def post_posterize(img, q=32):
    """
    POST-EFECTO — Posterización.
    Reduce la profundidad de color cuantizando a pasos de 'q'.
    Fórmula: (valor // q) * q  →  paleta de 256/q niveles por canal.
    """
    q = max(1, int(q))
    return ((img // q) * q).astype(np.uint8)


# ─────────────────────────────────────────────
# FONDO PROCEDURAL COMPARTIDO
# ─────────────────────────────────────────────

def background_hsv_gradient(img, t, hue0=10, hue1=140):
    """
    Rellena 'img' con un degradado vertical animado en espacio HSV.
    El tono (hue) varía de hue0 (arriba) a hue1 (abajo) más una
    perturbación senoidal en el tiempo para dar sensación de movimiento.
    """
    hsv = np.zeros((H, W, 3), np.uint8)
    ys  = np.linspace(0, 1, H, dtype=np.float32)   # posición normalizada fila
    # Tono: interpolación lineal + oscilación en t
    hue = (hue0 + (hue1 - hue0) * ys + 10 * np.sin(t * 0.4 + ys * 2.0)).astype(np.float32)
    hsv[:, :, 0] = np.clip(hue, 0, 179).astype(np.uint8)[:, None]   # H
    hsv[:, :, 1] = 200                                                # S fijo
    # Brillo: más oscuro hacia abajo (perspectiva de suelo)
    hsv[:, :, 2] = (40 + 120 * (1 - ys)).astype(np.uint8)[:, None]  # V
    img[:] = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


# ═══════════════════════════════════════════════════════════════
#  ESCENAS
# ═══════════════════════════════════════════════════════════════

# ── Escena 0: Créditos / Intro ────────────────────────────────

def scene_credits(img, t):
    """
    Escena introductoria con fondo estrellado y texto superpuesto.

    Técnicas usadas
    ---------------
    • Degradado HSV procedural (fondo cósmico azul-morado).
    • Estrellas con posiciones deterministas (semilla fija → reproducible).
    • GaussianBlur para suavizar el fondo.
    • cv2.putText para el "logo" del demo.
    """
    background_hsv_gradient(img, t, hue0=165, hue1=105)

    # Estrellas: posiciones pseudoaleatorias fijas (misma semilla cada frame)
    rng = np.random.default_rng(1)
    xs  = rng.integers(0, W, 380)
    ys  = rng.integers(0, int(H * 0.65), 380)
    img[ys, xs] = (255, 255, 255)                   # píxeles blancos = estrellas

    # Blur leve para "brillo" difuso
    img[:] = cv2.GaussianBlur(img, (0, 0), 0.6)

    # Texto principal centrado
    cv2.putText(img, "DEMO PROCEDURAL (GRAFICACION)",
                (42, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.95,
                (245, 245, 245), 2, cv2.LINE_AA)
    cv2.putText(img, "OpenCV + Matematicas",
                (42, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.85,
                (220, 220, 220), 2, cv2.LINE_AA)


# ── Escena 1: Curva de Lissajous ─────────────────────────────

def scene_lissajous(img, t):
    """
    CURVA PARAMÉTRICA 1 — Lissajous animada.
    Ecuaciones:
        x(t) = sin(a·t + δ)
        y(t) = sin(b·t)
    con a, b y δ variando suavemente en el tiempo para que la
    figura "respire" y no sea estática.

    La curva se dibuja con cv2.polylines sobre el degradado de fondo.
    """
    background_hsv_gradient(img, t, hue0=18, hue1=60)

    # Parámetros animados
    a     = 3 + 0.7 * math.sin(t * 0.6)
    b     = 2 + 0.7 * math.cos(t * 0.8)
    delta = math.pi / 2 + 0.4 * math.sin(t * 0.3)

    fx  = lambda x: np.sin(a * x + delta)
    fy  = lambda x: np.sin(b * x)
    pts = poly_param(fx, fy, 0, 2 * math.pi, 900, W * 0.5, H * 0.45, 260, 180)

    col = hsv_to_bgr(int(20 + 30 * np.sin(t * 0.8)), 210, 240)
    cv2.polylines(img, [pts], isClosed=False, color=col, thickness=2,
                  lineType=cv2.LINE_AA)


# ── Escena 2: Rosa Polar ──────────────────────────────────────

def scene_rose_polar(img, t):
    """
    CURVA PARAMÉTRICA 2 — Rosa polar (rhodonea).
    En coordenadas polares: r = cos(k·θ)
    Convertida a cartesianas:
        x(θ) = cos(k·θ) · cos(θ + θ₀)
        y(θ) = cos(k·θ) · sin(θ + θ₀)
    donde θ₀ = t·0.6  hace rotar la figura en el tiempo.

    Con k = 5 se obtienen 5 pétalos.
    Además se dibujan pequeños círculos animados (primitiva cv2.circle)
    como ornamento rítmico.
    """
    background_hsv_gradient(img, t, hue0=120, hue1=165)

    k      = 5
    theta0 = t * 0.6                                # rotación continua

    fx  = lambda th: np.cos(k * th) * np.cos(th + theta0)
    fy  = lambda th: np.cos(k * th) * np.sin(th + theta0)
    pts = poly_param(fx, fy, 0, 2 * math.pi, 1200, W * 0.5, H * 0.45, 240, 240)

    col = hsv_to_bgr(int(145 + 25 * np.sin(t * 0.5)), 220, 245)
    cv2.polylines(img, [pts], isClosed=False, color=col, thickness=2,
                  lineType=cv2.LINE_AA)

    # Círculos "beat" en la parte inferior — primitiva cv2.circle
    for i in range(6):
        r = int(18 + 10 * np.sin(t * 2.0 + i))
        cv2.circle(img,
                   center=(int(W * 0.18 + i * 110), int(H * 0.78)),
                   radius=max(1, r),
                   color=(230, 230, 230),
                   thickness=1,
                   lineType=cv2.LINE_AA)


# ── Escena 3: Espirógrafo (Hipotrocoide) ─────────────────────

def scene_spirograph(img, t):
    """
    CURVA PARAMÉTRICA 3 — Hipotrocoide (espirógrafo).
    Ecuaciones:
        x(t) = (R−r)·cos(t) + d·cos((R−r)/r · t + φ_x(t))
        y(t) = (R−r)·sin(t) − d·sin((R−r)/r · t + φ_y(t))
    donde φ_x y φ_y son perturbaciones lentas en el tiempo.

    POST-EFECTO: se aplica post_scanlines dentro de la escena
    para darle un look retro de monitor CRT.
    """
    background_hsv_gradient(img, t, hue0=80, hue1=20)

    R, r, d = 8.0, 3.0, 5.0
    w = (R - r) / r                                 # relación de velocidades angular

    fx  = lambda x: (R - r) * np.cos(x) + d * np.cos(w * x + 0.4 * np.sin(t * 0.7))
    fy  = lambda x: (R - r) * np.sin(x) - d * np.sin(w * x + 0.4 * np.cos(t * 0.6))
    pts = poly_param(fx, fy, 0, 14 * math.pi, 1600, W * 0.5, H * 0.46, 26, 26)

    col = hsv_to_bgr(int(10 + 140 * (0.5 + 0.5 * np.sin(t * 0.4))), 240, 240)
    cv2.polylines(img, [pts], isClosed=False, color=col, thickness=2,
                  lineType=cv2.LINE_AA)

    # Aplicar scanlines como parte del estilo visual de esta escena
    img[:] = post_scanlines(img, 0.18)


# ── Escena 4: Campo de Partículas ────────────────────────────

def scene_particles(img, t, rng):
    """
    CURVA PARAMÉTRICA 4 / TRANSFORMACIÓN — Campo de partículas.
    Cada partícula se desplaza siguiendo campos vectoriales senoidales:
        x'(t) = x + A·sin(y/λ₁ + ω₁·t) + B·cos(ω₂·t)
        y'(t) = y + C·cos(x/λ₂ + ω₃·t) + D·sin(ω₄·t)
    El módulo preserva las partículas dentro del canvas (operador %).

    La función rng.random() produce posiciones base que luego son
    deformadas —esto ilustra el concepto de "traslación continua
    no lineal" como transformación de campo.
    """
    background_hsv_gradient(img, t, hue0=150, hue1=100)

    n  = 1200
    xs = rng.random(n) * W
    ys = rng.random(n) * H

    # Desplazamiento por campo vectorial senoidal (traslación no lineal)
    xs = (xs + 110 * np.sin(ys / 55.0 + t * 1.7) + 40 * np.cos(t * 0.7)) % W
    ys = (ys + 85  * np.cos(xs / 75.0 + t * 1.2) + 30 * np.sin(t * 0.9)) % H

    v   = 0.5 + 0.5 * math.sin(t * 1.9)           # "velocidad" para modular brillo
    col = hsv_to_bgr(int(95 + 40 * math.sin(t * 0.8)), 210, int(210 + 40 * v))

    # Escritura directa en el buffer (píxeles individuales)
    img[ys.astype(np.int32), xs.astype(np.int32)] = col

    # Blur leve para simular persistencia retiniana / motion blur barato
    img[:] = cv2.GaussianBlur(img, (0, 0), 1.1)


# ── Escena 5: Fuego Procedural ────────────────────────────────

def scene_fire(img, t, state):
    """
    CURVA / SIMULACIÓN — Fuego procedural con mapa de calor.
    Algoritmo:
        1. El "heatmap" (float32) decae cada frame: heat *= 0.93
        2. Se inyectan valores aleatorios en la base (suelo = fuente de calor).
        3. Se aplica GaussianBlur para difundir el calor lateralmente.
        4. El mapa se desplaza 2 filas hacia arriba simulando convección.
        5. El heatmap se convierte a color HSV:
               H ∈ [0, 20]  → rojo a naranja
               S ∈ [140, 220]
               V ∈ [60, 255] → oscuro a brillante
        6. Se superponen chispas blancas (píxeles aleatorios).

    TRANSFORMACIÓN usada: desplazamiento (traslación) de filas del buffer
    para simular la subida del calor (heat[:-2] = heat[2:]).
    """
    heat = state["heat"]
    rng  = state["rng"]

    # ── 1. Enfriamiento global
    heat[:] = (heat * 0.93).astype(np.float32)

    # ── 2. Inyección de calor en la base
    base_n = 1400
    xs = rng.integers(0, W, base_n)
    ys = rng.integers(int(H * 0.82), H, base_n)
    heat[ys, xs] += rng.random(base_n) * (0.8 + 0.6 * (0.5 + 0.5 * math.sin(t * 2.0)))

    # ── 3. Difusión lateral (blur anisotrópico)
    heat[:] = cv2.GaussianBlur(heat, (0, 0), 2.2)

    # ── 4. TRANSFORMACIÓN: traslación hacia arriba (convección barata)
    heat[:-2, :] = heat[2:, :]     # cada fila copia la fila 2 posiciones abajo
    heat[-2:, :] = 0.0             # la base se reinicia (se re-inyectará)

    # ── 5. Mapeo HSV → BGR
    h   = (20  - 20  * np.clip(heat, 0, 1)).astype(np.uint8)   # tono: rojo-naranja
    s   = (220 - 80  * np.clip(heat, 0, 1)).astype(np.uint8)   # saturación alta
    v   = (60  + 195 * np.clip(heat, 0, 1)).astype(np.uint8)   # valor: oscuro→brillante
    hsv = np.dstack([h, s, v]).astype(np.uint8)
    img[:] = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    # ── 6. Silueta oscura en el suelo + chispas blancas
    cv2.rectangle(img, (0, int(H * 0.83)), (W, H), (10, 10, 10), -1)
    sparks = 160
    sx = rng.integers(0, W, sparks)
    sy = rng.integers(int(H * 0.55), int(H * 0.9), sparks)
    img[sy, sx] = (255, 255, 255)
    img[:] = cv2.GaussianBlur(img, (0, 0), 0.6)


# ─────────────────────────────────────────────
# DISPATCHER DE ESCENAS
# ─────────────────────────────────────────────

def render_scene(buf, scene_id, t, rng, fire_state):
    """
    Enruta al render de la escena correspondiente según scene_id (0–5).
    Cada escena recibe el buffer de imagen, el tiempo 't' y estado
    opcional (rng para partículas, fire_state para fuego).
    """
    if   scene_id == 0: scene_credits(buf, t)
    elif scene_id == 1: scene_lissajous(buf, t)
    elif scene_id == 2: scene_rose_polar(buf, t)
    elif scene_id == 3: scene_spirograph(buf, t)
    elif scene_id == 4: scene_particles(buf, t, rng)
    else:               scene_fire(buf, t, fire_state)


# ─────────────────────────────────────────────
# TIMELINE — GESTOR DE ESCENAS Y TRANSICIONES
# ─────────────────────────────────────────────

def timeline(t, rng, bufA, bufB, fire_state):
    """
    Decide qué escena mostrar en el instante 't' y aplica
    las transiciones entre ellas.

    Estructura temporal
    -------------------
    • 6 escenas × 10 s = 60 s totales.
    • Cada escena ocupa un "bloque" de 10 s.
    • En los últimos 1.2 s de cada bloque se hace crossfade al
      siguiente usando cv2.addWeighted (composición por capas).
    • Un destello ("flash") blanco al final refuerza el corte.
    • Fade-in global en los primeros 1.5 s y fade-out en los
      últimos 1.5 s.

    TRANSFORMACIONES visibles aquí
    --------------------------------
    • cv2.addWeighted: mezcla alfa entre dos buffers (composición).
    • Multiplicación escalar del frame (fade).
    """
    # Bloque activo (0–5) según tiempo lineal
    block = int(min(5, max(0, t // 10)))
    t_in  = t - block * 10                          # tiempo local dentro del bloque

    # Render de la escena base en bufA
    render_scene(bufA, block, t, rng, fire_state)
    frame = bufA

    # ── Crossfade hacia la siguiente escena (últimos 1.2 s del bloque)
    if block < 5 and t_in >= 8.8:
        render_scene(bufA, block,     t, rng, fire_state)
        render_scene(bufB, block + 1, t, rng, fire_state)

        a     = smoothstep(8.8, 10.0, t_in)        # progreso de la transición [0,1]
        # COMPOSICIÓN POR CAPAS: alpha-blend de dos buffers
        frame = cv2.addWeighted(bufA, 1 - a, bufB, a, 0)

        # Flash blanco al final de la transición
        flash = smoothstep(9.6, 10.0, t_in)
        if flash > 0:
            frame = cv2.addWeighted(frame, 1.0,
                                    np.full_like(frame, 255), 0.12 * flash, 0)

    # ── Fade in/out global
    fin  = smoothstep(0.0,              1.5,      t)
    fout = 1.0 - smoothstep(DURATION - 1.5, DURATION, t)
    f    = fin * fout
    if f < 0.999:
        frame = (frame.astype(np.float32) * f).astype(np.uint8)

    return frame


# ─────────────────────────────────────────────
# BUCLE PRINCIPAL
# ─────────────────────────────────────────────

def main():
    """
    Punto de entrada.
    Modos:
        python demo.py            → visualización en ventana (ESC para salir)
        python demo.py --export   → exporta demo_output.mp4

    Flujo por frame
    ---------------
    1. timeline() → frame con escena y transición.
    2. post_vignette()  → oscurece bordes.
    3. post_scanlines() → efecto CRT.
    4. post_posterize() → reduce paleta (look retro / poster).
    5. imshow() o VideoWriter.write().
    """
    parser = argparse.ArgumentParser(description="Demo Procedural OpenCV")
    parser.add_argument("--export", action="store_true",
                        help="Exportar video MP4 en lugar de mostrarlo en pantalla")
    args = parser.parse_args()

    # Generadores de números aleatorios con semilla fija (reproducibilidad)
    rng        = np.random.default_rng(123)
    fire_state = {
        "heat": np.zeros((H, W), np.float32),       # mapa de calor del fuego
        "rng" : np.random.default_rng(999),          # rng exclusivo para el fuego
    }

    # Buffers de imagen reutilizables (evita allocations por frame)
    bufA = np.zeros((H, W, 3), np.uint8)
    bufB = np.zeros((H, W, 3), np.uint8)

    total_frames = int(DURATION * FPS)              # 60 s × 30 FPS = 1800 frames

    # ── Configuración del exportador de video (opcional)
    writer = None
    if args.export:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter("demo_output.mp4", fourcc, FPS, (W, H))
        print(f"Exportando {total_frames} frames → demo_output.mp4 ...")

    t0 = time.perf_counter()

    for i in range(total_frames):
        t = i / FPS                                  # tiempo en segundos

        # ── 1. Generar frame con timeline y transiciones
        frame = timeline(t, rng, bufA, bufB, fire_state)

        # ── 2. Post-efectos globales (se aplican sobre TODOS los frames)
        frame = post_vignette(frame, 0.72)           # viñeta oscura en bordes
        frame = post_scanlines(frame, 0.16)          # líneas CRT sutiles
        frame = post_posterize(frame, 24)            # paleta reducida (24 pasos)

        # ── 3. Salida
        if writer:
            writer.write(frame)
            if i % FPS == 0:
                print(f"  Frame {i:4d}/{total_frames}  t={t:5.1f}s")
        else:
            cv2.imshow("Proyecto Final: demo procedural (OpenCV)", frame)
            if cv2.waitKey(1) & 0xFF == 27:          # ESC = salir anticipado
                break

    elapsed = time.perf_counter() - t0
    print(f"Tiempo total de render: {elapsed:.1f} s")

    if writer:
        writer.release()
        print("Video guardado como demo_output.mp4")
    else:
        cv2.destroyAllWindows()


# ─────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────
if __name__ == "__main__":
    main()