"""
Realidad aumentada — marcador ArUco + OpenGL (GLFW).
Video de webcam como fondo; objeto 3D (tetera GLUT o esfera GLU) anclado al marcador.

Entorno (ejemplo):
  source /home/likcos/entornos/programacion/bin/activate
  python /home/likcos/Scripts/ar_ra_marcador_opengl_glfw.py

Requisitos: opencv-python (o opencv-contrib-python), PyOpenGL, glfw, numpy.
Imprime el marcador con el script generar_marcador_aruco.py o el bloque del .org.

Controles:
  T     alternar tetera / esfera
  +/-   escala del modelo 3D
  ESC Q salir
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import glfw
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import (
    GLU_FILL,
    gluNewQuadric,
    gluQuadricDrawStyle,
    gluSphere,
)

# ---------------------------------------------------------------------------
# Configuración (alumnos: tocar aquí)
# ---------------------------------------------------------------------------
CAMERA_INDEX = 0
MARKER_LENGTH_M = 0.10  # lado del marcador impreso en metros (ej. 10 cm)
ARUCO_DICT = cv2.aruco.DICT_4X4_50
MARKER_ID = 0  # ID del marcador impreso (generateImageMarker id=0)
MODEL_SCALE = 0.04  # escala del objeto respecto al marcador
OBJECT_MODE = "sphere"  # "teapot" | "sphere"
WINDOW_TITLE = "RA: ArUco + OpenGL (T=tetera/esfera, ESC=salir)"
ZNear, ZFar = 0.01, 100.0

SCRIPT_DIR = Path(__file__).resolve().parent
CALIB_NPZ = SCRIPT_DIR / "camera_ar.npz"


def default_camera_matrix(width: int, height: int) -> np.ndarray:
    f = float(max(width, height))
    cx, cy = width / 2.0, height / 2.0
    return np.array([[f, 0, cx], [0, f, cy], [0, 0, 1]], dtype=np.float64)


def load_calibration(width: int, height: int):
    if CALIB_NPZ.is_file():
        data = np.load(CALIB_NPZ)
        return data["camera_matrix"], data["dist_coeffs"]
    return default_camera_matrix(width, height), np.zeros((5, 1), dtype=np.float64)


def make_aruco_detector():
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    params = cv2.aruco.DetectorParameters()
    if hasattr(cv2.aruco, "ArucoDetector"):
        return cv2.aruco.ArucoDetector(dictionary, params), dictionary
    return None, dictionary


def detect_marker(gray, detector, dictionary):
    if detector is not None:
        corners, ids, _ = detector.detectMarkers(gray)
    else:
        corners, ids, _ = cv2.aruco.detectMarkers(
            gray, dictionary, parameters=cv2.aruco.DetectorParameters()
        )
    if ids is None or len(ids) == 0:
        return None, None, None
    idx = 0
    if MARKER_ID is not None:
        matches = np.where(ids.flatten() == MARKER_ID)[0]
        if len(matches) == 0:
            return None, None, None
        idx = int(matches[0])
    return corners[idx], ids[idx], idx


def marker_object_points(side_length):
    s = side_length / 2.0
    return np.array([[-s, s, 0], [s, s, 0], [s, -s, 0], [-s, -s, 0]], dtype=np.float32)


def estimate_pose(corners, camera_matrix, dist_coeffs):
    image_points = corners[0] if corners.ndim == 3 else corners
    image_points = np.asarray(image_points, dtype=np.float32).reshape(-1, 2)
    obj_pts = marker_object_points(MARKER_LENGTH_M)
    flags = cv2.SOLVEPNP_IPPE_SQUARE if hasattr(cv2, "SOLVEPNP_IPPE_SQUARE") else cv2.SOLVEPNP_ITERATIVE
    ok, rvec, tvec = cv2.solvePnP(obj_pts, image_points, camera_matrix, dist_coeffs, flags=flags)
    if not ok:
        raise RuntimeError("solvePnP falló")
    return rvec, tvec


def projection_from_k(K, width, height, znear, zfar):
    fx, fy = K[0, 0], K[1, 1]
    cx, cy = K[0, 2], K[1, 2]
    P = np.zeros((4, 4), dtype=np.float32)
    P[0, 0] = 2.0 * fx / width
    P[1, 1] = 2.0 * fy / height
    P[0, 2] = (width - 2.0 * cx) / width
    P[1, 2] = (2.0 * cy - height) / height
    P[2, 2] = -(zfar + znear) / (zfar - znear)
    P[2, 3] = -1.0
    P[3, 2] = -2.0 * zfar * znear / (zfar - znear)
    return P


def modelview_from_pose(rvec, tvec) -> np.ndarray:
    R, _ = cv2.Rodrigues(rvec)
    M = np.eye(4, dtype=np.float64)
    M[:3, :3] = R
    M[:3, 3] = tvec.flatten()
    cv_to_gl = np.diag([1.0, -1.0, -1.0, 1.0])
    return (cv_to_gl @ M).T.astype(np.float32)


_quadric = None
_glut_ready = False


def init_glut_for_geometry():
    global _glut_ready
    if _glut_ready:
        return
    from OpenGL.GLUT import glutInit
    glutInit(sys.argv if sys.argv else [""])
    _glut_ready = True


def draw_sphere(radius: float = 1.0) -> None:
    global _quadric
    if _quadric is None:
        _quadric = gluNewQuadric()
        gluQuadricDrawStyle(_quadric, GLU_FILL)
    gluSphere(_quadric, radius, 32, 16)


def draw_teapot(scale: float) -> None:
    from OpenGL.GLUT import glutSolidTeapot
    glutSolidTeapot(scale)


def draw_ar_object(mode: str, scale: float) -> None:
    glPushMatrix()
    glTranslatef(0.0, 0.0, scale * 0.5)
    if mode == "sphere":
        glColor3f(0.35, 0.75, 1.0)
        draw_sphere(scale)
    else:
        glColor3f(0.85, 0.45, 0.25)
        draw_teapot(scale)
    glPopMatrix()


def setup_lighting() -> None:
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightfv(GL_LIGHT0, GL_POSITION, (0.2, 0.4, 1.0, 0.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 0.95, 1.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.25, 0.25, 0.25, 1.0))
    glEnable(GL_NORMALIZE)


_tex_id = None
_tex_buf = None


def upload_frame_texture(frame_bgr, width, height) -> None:
    global _tex_id, _tex_buf
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    rgb = cv2.flip(rgb, 0)
    if _tex_buf is None or _tex_buf.shape[:2] != (height, width):
        _tex_buf = np.empty((height, width, 3), dtype=np.uint8)
    np.copyto(_tex_buf, rgb)
    if _tex_id is None:
        _tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, _tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(
        GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, _tex_buf
    )


def draw_background_quad(width, height) -> None:
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, width, 0, height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, _tex_id)
    glColor3f(1, 1, 1)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex2f(0, 0)
    glTexCoord2f(1, 0)
    glVertex2f(width, 0)
    glTexCoord2f(1, 1)
    glVertex2f(width, height)
    glTexCoord2f(0, 1)
    glVertex2f(0, height)
    glEnd()
    glDisable(GL_TEXTURE_2D)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)


def draw_scene_3d(rvec, tvec, camera_matrix, width, height, mode, scale) -> None:
    P = projection_from_k(camera_matrix, width, height, ZNear, ZFar)
    MV = modelview_from_pose(rvec, tvec)
    glMatrixMode(GL_PROJECTION)
    glLoadMatrixf(P)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glMultMatrixf(MV)
    setup_lighting()
    draw_ar_object(mode, scale)


def main() -> None:
    global OBJECT_MODE, MODEL_SCALE

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("No se pudo abrir la cámara.", file=sys.stderr)
        sys.exit(1)

    ret, probe = cap.read()
    if not ret:
        sys.exit(1)

    cam_h, cam_w = probe.shape[:2]
    camera_matrix, dist_coeffs = load_calibration(cam_w, cam_h)
    detector, dictionary = make_aruco_detector()

    if OBJECT_MODE == "teapot":
        init_glut_for_geometry()

    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    window = glfw.create_window(cam_w, cam_h, WINDOW_TITLE, None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.swap_interval(1)

    def on_key(win, key, _scancode, action, _mods):
        global OBJECT_MODE, MODEL_SCALE
        if action != glfw.PRESS:
            return
        if key in (glfw.KEY_ESCAPE, glfw.KEY_Q):
            glfw.set_window_should_close(win, True)
        elif key == glfw.KEY_T:
            OBJECT_MODE = "sphere" if OBJECT_MODE == "teapot" else "teapot"
            if OBJECT_MODE == "teapot":
                init_glut_for_geometry()
        elif key in (glfw.KEY_EQUAL, glfw.KEY_KP_ADD):
            MODEL_SCALE *= 1.1
        elif key in (glfw.KEY_MINUS, glfw.KEY_KP_SUBTRACT):
            MODEL_SCALE /= 1.1

    glfw.set_key_callback(window, on_key)
    glEnable(GL_DEPTH_TEST)

    while not glfw.window_should_close(window):
        ret, frame = cap.read()
        if not ret:
            continue
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, _, _ = detect_marker(gray, detector, dictionary)

        glViewport(0, 0, w, h)
        upload_frame_texture(frame, w, h)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        draw_background_quad(w, h)

        if corners is not None:
            rvec, tvec = estimate_pose(corners, camera_matrix, dist_coeffs)
            draw_scene_3d(rvec, tvec, camera_matrix, w, h, OBJECT_MODE, MODEL_SCALE)

        glfw.swap_buffers(window)
        glfw.poll_events()

    cap.release()
    glfw.terminate()


if __name__ == "__main__":
    main()