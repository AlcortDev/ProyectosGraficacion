"""
Ciudad 3D - Proyecto de Graficación por Computadora
Entorno 3D con control de cámara mediante detección de manos (MediaPipe 0.10+)

ANTES DE EJECUTAR — descarga el modelo de manos (solo una vez):
  python descarga_modelo.py
  (o manualmente desde https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task)

Instalación de dependencias:
  pip install PyOpenGL PyOpenGL_accelerate pygame mediapipe opencv-python numpy

Controles de teclado (alternativos a la cámara):
  Flechas    → rotar cámara
  +/-        → zoom
  ESC        → salir
"""

import sys, os, math, time, threading
import numpy as np
import cv2
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.vision import RunningMode

# ─────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────
WIDTH, HEIGHT   = 1280, 720
MODEL_PATH      = "hand_landmarker.task"   # debe estar en la misma carpeta

# ─────────────────────────────────────────────
#  ESTADO COMPARTIDO DE CÁMARA
# ─────────────────────────────────────────────
cam_lock  = threading.Lock()
cam_state = {
    "angle_h":      0.0,
    "angle_v":      25.0,
    "distance":     40.0,
    "hand_detected": False,
    "gesture":      "none",
}

# ─────────────────────────────────────────────
#  HILO MEDIAPIPE (nueva API 0.10+)
# ─────────────────────────────────────────────

def hand_thread():
    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR] No se encontró el modelo '{MODEL_PATH}'.")
        print("Ejecuta primero:  python descarga_modelo.py")
        print("El programa continuará sin detección de manos.")
        print("Usa las teclas de flechas para rotar la cámara.")
        return

    base_opts = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
    opts = mp_vision.HandLandmarkerOptions(
        base_options=base_opts,
        running_mode=RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  300)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 200)

    prev_x, prev_y = None, None
    timestamp_ms   = 0

    with mp_vision.HandLandmarker.create_from_options(opts) as landmarker:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            timestamp_ms += int(1000 / 30)

            # Convertir a MediaPipe Image
            rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = landmarker.detect_for_video(mp_img, timestamp_ms)

            if result.hand_landmarks:
                lm = result.hand_landmarks[0]   # lista de NormalizedLandmark

                # Dibujar esqueleto manualmente
                h, w = frame.shape[:2]
                pts = [(int(p.x * w), int(p.y * h)) for p in lm]
                connections = [
                    (0,1),(1,2),(2,3),(3,4),
                    (0,5),(5,6),(6,7),(7,8),
                    (0,9),(9,10),(10,11),(11,12),
                    (0,13),(13,14),(14,15),(15,16),
                    (0,17),(17,18),(18,19),(19,20),
                    (5,9),(9,13),(13,17),
                ]
                for a, b in connections:
                    cv2.line(frame, pts[a], pts[b], (0, 200, 0), 2)
                for p in pts:
                    cv2.circle(frame, p, 4, (0, 255, 0), -1)

                # Posición landmark 9 (base dedo medio)
                x_norm = lm[9].x
                y_norm = lm[9].y

                # Gesto: detectar puño (puntas debajo de sus nudillos)
                tips = [8, 12, 16, 20]
                mcps = [5,  9, 13, 17]
                closed = all(lm[t].y > lm[m].y for t, m in zip(tips, mcps))

                with cam_lock:
                    cam_state["hand_detected"] = True
                    cam_state["gesture"] = "closed" if closed else "open"

                    if prev_x is not None:
                        dx = (x_norm - prev_x) * 180.0
                        dy = (y_norm - prev_y) * 90.0
                        if closed:
                            cam_state["distance"] = max(
                                10.0, min(120.0, cam_state["distance"] + dy * 2))
                        else:
                            cam_state["angle_h"] += dx
                            cam_state["angle_v"]  = max(
                                5.0, min(85.0, cam_state["angle_v"] + dy))

                prev_x, prev_y = x_norm, y_norm

                label = "PUNO: zoom" if closed else "ABIERTA: rotar"
                cv2.putText(frame, label, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            else:
                prev_x, prev_y = None, None
                with cam_lock:
                    cam_state["hand_detected"] = False
                    cam_state["gesture"] = "none"

            cv2.imshow("Camara – Control de manos", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

    cap.release()
    cv2.destroyAllWindows()


# ─────────────────────────────────────────────
#  PRIMITIVAS OpenGL
# ─────────────────────────────────────────────

def draw_floor(size=60, step=4):
    glBegin(GL_QUADS)
    glColor3f(0.18, 0.28, 0.18)
    glVertex3f(-size,0,-size); glVertex3f(size,0,-size)
    glVertex3f(size,0,size);   glVertex3f(-size,0,size)
    glEnd()
    glColor3f(0.25, 0.38, 0.25)
    glBegin(GL_LINES)
    for i in range(-size, size+1, step):
        glVertex3f(i,0.01,-size); glVertex3f(i,0.01,size)
        glVertex3f(-size,0.01,i); glVertex3f(size,0.01,i)
    glEnd()

def draw_box(w, h, d):
    hw,hh,hd = w/2,h/2,d/2
    v = [(-hw,-hh,-hd),(hw,-hh,-hd),(hw,hh,-hd),(-hw,hh,-hd),
         (-hw,-hh,hd),(hw,-hh,hd),(hw,hh,hd),(-hw,hh,hd)]
    faces = [(0,1,2,3),(4,5,6,7),(0,4,7,3),(1,5,6,2),(0,1,5,4),(3,2,6,7)]
    glBegin(GL_QUADS)
    for f in faces:
        for vi in f: glVertex3fv(v[vi])
    glEnd()
    glColor3f(0,0,0)
    edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
    glBegin(GL_LINES)
    for e in edges:
        for vi in e: glVertex3fv(v[vi])
    glEnd()

def draw_cylinder(radius, height, slices=16):
    step   = 2*math.pi/slices
    angles = [i*step for i in range(slices+1)]
    glBegin(GL_QUAD_STRIP)
    for a in angles:
        glVertex3f(radius*math.cos(a),0,      radius*math.sin(a))
        glVertex3f(radius*math.cos(a),height, radius*math.sin(a))
    glEnd()
    glBegin(GL_TRIANGLE_FAN); glVertex3f(0,0,0)
    for a in angles: glVertex3f(radius*math.cos(a),0,radius*math.sin(a))
    glEnd()
    glBegin(GL_TRIANGLE_FAN); glVertex3f(0,height,0)
    for a in angles: glVertex3f(radius*math.cos(a),height,radius*math.sin(a))
    glEnd()

def draw_cone(radius, height, slices=16):
    step   = 2*math.pi/slices
    angles = [i*step for i in range(slices+1)]
    glBegin(GL_TRIANGLE_FAN); glVertex3f(0,height,0)
    for a in angles: glVertex3f(radius*math.cos(a),0,radius*math.sin(a))
    glEnd()
    glBegin(GL_TRIANGLE_FAN); glVertex3f(0,0,0)
    for a in angles: glVertex3f(radius*math.cos(a),0,radius*math.sin(a))
    glEnd()

def draw_sphere(radius, slices=12, stacks=12):
    q = gluNewQuadric(); gluSphere(q,radius,slices,stacks); gluDeleteQuadric(q)

def draw_road(x1,z1,x2,z2,width=3):
    dx,dz = x2-x1,z2-z1
    length = math.sqrt(dx*dx+dz*dz)
    nx,nz  = -dz/length*width/2, dx/length*width/2
    glColor3f(0.15,0.15,0.15)
    glBegin(GL_QUADS)
    glVertex3f(x1+nx,0.02,z1+nz); glVertex3f(x2+nx,0.02,z2+nz)
    glVertex3f(x2-nx,0.02,z2-nz); glVertex3f(x1-nx,0.02,z1-nz)
    glEnd()


# ─────────────────────────────────────────────
#  CLASES DE OBJETOS
# ─────────────────────────────────────────────

class CityObject:
    def __init__(self, x, z, **kw):
        self.x=x; self.z=z
        self.phase = kw.get("phase",0.0)
        self.speed = kw.get("speed",1.0)
        self.color = kw.get("color",(0.5,0.5,0.5))
        self.color2= kw.get("color2",(0.7,0.7,0.7))
        self.t     = self.phase
    def update(self,dt): self.t += dt*self.speed
    def draw(self): pass


class Building(CityObject):
    def __init__(self,x,z,w,h,d,**kw):
        super().__init__(x,z,**kw); self.w=w; self.h=h; self.d=d
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x,0,self.z)
        glRotatef(math.sin(self.t)*0.3, 0,0,1)
        glTranslatef(0,self.h/2,0)
        glColor3fv(self.color); draw_box(self.w,self.h,self.d)
        rows = max(1,int(self.h/2)); cols = max(1,int(self.w/1.5))
        glColor3f(1.0,0.95,0.4)
        for r in range(rows):
            for c in range(cols):
                wx = -self.w/2+(c+0.5)*self.w/cols
                wy = -self.h/2+(r+0.6)*self.h/rows
                glPushMatrix(); glTranslatef(wx,wy,self.d/2+0.05)
                draw_box(0.3,0.4,0.05); glPopMatrix()
        glPopMatrix()


class Tower(CityObject):
    def draw(self):
        glPushMatrix(); glTranslatef(self.x,0,self.z)
        glColor3fv(self.color)
        glPushMatrix(); glTranslatef(0,5,0); draw_box(3,10,3); glPopMatrix()
        glColor3fv(self.color2)
        glPushMatrix(); glTranslatef(0,12,0); draw_box(2,4,2); glPopMatrix()
        glPushMatrix(); glTranslatef(0,14,0); glRotatef(self.t*60,0,1,0)
        glColor3f(1,0,0); draw_box(4,0.2,0.2)
        glColor3f(0,0.5,1); draw_box(0.2,0.2,4); glPopMatrix()
        glColor3f(0.8,0.1,0.1)
        glPushMatrix(); glTranslatef(0,14,0); draw_cylinder(0.1,3); glPopMatrix()
        glPopMatrix()


class Tree(CityObject):
    def draw(self):
        glPushMatrix(); glTranslatef(self.x,0,self.z)
        glColor3f(0.45,0.25,0.1); draw_cylinder(0.2,2)
        glTranslatef(0,1.5,0); glRotatef(math.sin(self.t*1.5)*2,0,0,1)
        glColor3fv(self.color)
        glPushMatrix(); draw_cone(1.2,2.5); glPopMatrix()
        glColor3fv(self.color2)
        glPushMatrix(); glTranslatef(0,1.5,0); draw_cone(0.9,2.0); glPopMatrix()
        glColor3f(0.1,0.7,0.1)
        glPushMatrix(); glTranslatef(0,2.8,0); draw_cone(0.6,1.5); glPopMatrix()
        glPopMatrix()


class Streetlight(CityObject):
    def draw(self):
        glPushMatrix(); glTranslatef(self.x,0,self.z)
        glColor3f(0.3,0.3,0.3); draw_cylinder(0.1,4)
        glTranslatef(0,4,0)
        glPushMatrix(); glRotatef(90,0,0,1); draw_cylinder(0.08,0.8); glPopMatrix()
        blink = abs(math.sin(self.t*2.0))
        glColor3f(1.0,0.9*blink,0.2*blink)
        glTranslatef(-0.8,0,0); draw_sphere(0.2)
        glPopMatrix()


class Car(CityObject):
    def __init__(self,x,z,radius,**kw):
        super().__init__(x,z,**kw); self.radius=radius
    def update(self,dt):
        super().update(dt)
        self.x = math.cos(self.t)*self.radius
        self.z = math.sin(self.t)*self.radius
    def draw(self):
        glPushMatrix(); glTranslatef(self.x,0.4,self.z)
        heading = math.degrees(math.atan2(
            math.sin(self.t+0.01)-math.sin(self.t),
            math.cos(self.t+0.01)-math.cos(self.t)))
        glRotatef(-heading,0,1,0)
        glColor3fv(self.color); draw_box(2.2,0.7,1.2)
        glColor3fv(self.color2)
        glPushMatrix(); glTranslatef(0,0.6,0); draw_box(1.2,0.6,1.0); glPopMatrix()
        glColor3f(0.1,0.1,0.1)
        ws = self.t*200
        for wx,wz in [(-0.7,0.65),(0.7,0.65),(-0.7,-0.65),(0.7,-0.65)]:
            glPushMatrix(); glTranslatef(wx,-0.3,wz); glRotatef(ws,1,0,0)
            draw_cylinder(0.28,0.15); glPopMatrix()
        glPopMatrix()


class Fountain(CityObject):
    def __init__(self,x,z,**kw):
        super().__init__(x,z,**kw)
        rng = np.random.default_rng(42); n=30
        self.angles  = rng.uniform(0,2*math.pi,n)
        self.speeds  = rng.uniform(0.5,1.5,n)
        self.offsets = rng.uniform(0,2*math.pi,n)
    def draw(self):
        glPushMatrix(); glTranslatef(self.x,0,self.z)
        glColor3f(0.6,0.6,0.65); draw_cylinder(2.0,0.4)
        glTranslatef(0,0.4,0)
        glColor3f(0.55,0.55,0.6); draw_cylinder(0.3,1.5)
        glColor4f(0.2,0.5,1.0,0.7)
        for ang,spd,off in zip(self.angles,self.speeds,self.offsets):
            tl = self.t*spd+off
            r  = math.sin(tl)*1.5; y = abs(math.cos(tl))*2.0
            glPushMatrix(); glTranslatef(r*math.cos(ang),y+1.5,r*math.sin(ang))
            draw_sphere(0.08); glPopMatrix()
        glPopMatrix()


class Windmill(CityObject):
    def draw(self):
        glPushMatrix(); glTranslatef(self.x,0,self.z)
        glColor3f(0.8,0.75,0.65); draw_cylinder(0.5,6,slices=8)
        glTranslatef(0,6,0)
        glPushMatrix(); glRotatef(self.t*90,0,0,1)
        glColor3fv(self.color)
        for k in range(4):
            glPushMatrix(); glRotatef(k*90,0,0,1); glTranslatef(1.5,0,0)
            draw_box(2.5,0.3,0.1); glPopMatrix()
        glPopMatrix(); glPopMatrix()


class Balloon(CityObject):
    def draw(self):
        y = 10+math.sin(self.t*0.8+self.phase)*3
        glPushMatrix(); glTranslatef(self.x,y,self.z)
        glColor3f(0.55,0.35,0.1)
        glPushMatrix(); glTranslatef(0,-2.3,0); draw_box(0.7,0.5,0.7); glPopMatrix()
        glColor3f(0.3,0.2,0.05)
        glBegin(GL_LINES)
        for cx,cz in [(-0.3,-0.3),(0.3,-0.3),(-0.3,0.3),(0.3,0.3)]:
            glVertex3f(cx,-2.0,cz); glVertex3f(0,0,0)
        glEnd()
        glColor3fv(self.color); draw_sphere(1.2)
        glPopMatrix()


class Stadium(CityObject):
    def draw(self):
        glPushMatrix(); glTranslatef(self.x,0,self.z); sl=24
        glColor3f(0.1,0.6,0.1)
        glBegin(GL_TRIANGLE_FAN); glVertex3f(0,0.1,0)
        for i in range(sl+1):
            a=2*math.pi*i/sl; glVertex3f(3.5*math.cos(a),0.1,2.5*math.sin(a))
        glEnd()
        for lvl in range(3):
            rx=4.0+lvl*0.8; rz=3.0+lvl*0.6; h=0.5+lvl*0.8
            glColor3f(0.7-lvl*0.1,0.7-lvl*0.1,0.75)
            glBegin(GL_QUAD_STRIP)
            for i in range(sl+1):
                a=2*math.pi*i/sl
                glVertex3f(rx*math.cos(a),0,rz*math.sin(a))
                glVertex3f(rx*math.cos(a),h,rz*math.sin(a))
            glEnd()
        blink=int(self.t*2)%2
        glColor3f(1.0,blink*0.8,0.0)
        glPushMatrix(); glTranslatef(0,5.5,0); draw_box(2,0.8,0.2); glPopMatrix()
        glPopMatrix()


class Pyramid(CityObject):
    def draw(self):
        glPushMatrix(); glTranslatef(self.x,0,self.z)
        glRotatef(self.t*30,0,1,0); s=3.0; h=4.0
        v = [(s,0,s),(-s,0,s),(-s,0,-s),(s,0,-s),(0,h,0)]
        cols=[self.color,self.color2,(0.9,0.7,0.1),(0.7,0.5,0.05)]
        glBegin(GL_TRIANGLES)
        for idx,f in enumerate([(0,1,4),(1,2,4),(2,3,4),(3,0,4)]):
            glColor3fv(cols[idx])
            for vi in f: glVertex3fv(v[vi])
        glEnd()
        glColor3f(0.3,0.25,0.1)
        glBegin(GL_QUADS)
        for vi in [0,3,2,1]: glVertex3fv(v[vi])
        glEnd(); glPopMatrix()


# ─────────────────────────────────────────────
#  CONSTRUCCIÓN DE LA CIUDAD
# ─────────────────────────────────────────────

def build_city():
    rng = np.random.default_rng(7)
    objects = []

    # 10 Edificios
    bd = [
        (-20,-20,4,14,4,(0.3,0.4,0.6)), (-14,-20,3,10,3,(0.5,0.3,0.3)),
        (-20,-12,5,18,5,(0.4,0.5,0.4)), (-20,  4,4,12,4,(0.6,0.5,0.3)),
        (-14, 14,3, 8,3,(0.4,0.4,0.6)), ( 14,-20,4,16,4,(0.3,0.5,0.5)),
        ( 20,-14,5,20,5,(0.5,0.4,0.3)), ( 14,  4,4,14,4,(0.6,0.3,0.4)),
        ( 20, 14,3,10,3,(0.3,0.6,0.4)), ( 14, 20,5,12,5,(0.5,0.5,0.3)),
    ]
    for x,z,w,h,d,col in bd:
        objects.append(Building(x,z,w,h,d, color=col,
            color2=tuple(min(1,c+0.15) for c in col),
            speed=0.3+rng.random()*0.3, phase=rng.random()*math.pi*2))

    # 3 Torres
    for x,z,col in [(-5,-25,(0.4,0.4,0.5)),(5,-25,(0.5,0.4,0.4)),(0,25,(0.4,0.5,0.4))]:
        objects.append(Tower(x,z, color=col,color2=(0.8,0.8,0.85),
            speed=1.0, phase=rng.random()*math.pi*2))

    # 5 Árboles
    for x,z in [(-8,-8),(-8,8),(8,-8),(8,8),(0,-10)]:
        objects.append(Tree(x,z,
            color=(0.1,0.55+rng.random()*0.2,0.1),
            color2=(0.05,0.45+rng.random()*0.2,0.05),
            speed=0.5+rng.random()*0.5, phase=rng.random()*math.pi*2))

    # 4 Farolas
    for x,z in [(-5,-5),(5,-5),(-5,5),(5,5)]:
        objects.append(Streetlight(x,z, speed=1.0+rng.random(), phase=rng.random()*math.pi*2))

    # 4 Coches (órbitas circulares)
    for ri,(radius,col) in enumerate([
        (12,(0.8,0.1,0.1)),(15,(0.1,0.1,0.8)),
        (18,(0.1,0.6,0.1)),(22,(0.9,0.6,0.0)),
    ]):
        objects.append(Car(radius,0,radius, color=col,
            color2=tuple(min(1,c+0.2) for c in col),
            speed=0.3+ri*0.1, phase=rng.random()*math.pi*2))

    # 1 Fuente
    objects.append(Fountain(0,0, speed=1.0, phase=0))

    # 2 Molinos
    objects.append(Windmill(-28, 0, color=(0.85,0.82,0.7), speed=1.5))
    objects.append(Windmill( 28, 0, color=(0.7,0.82,0.85), speed=1.2))

    # 3 Globos
    for i,col in enumerate([(1,0.2,0.2),(0.2,0.2,1),(1,0.8,0)]):
        objects.append(Balloon(-10+i*10,-30, color=col, speed=0.4, phase=i*2.1))

    # 1 Estadio
    objects.append(Stadium(-28,-28, speed=1.0))

    # 1 Pirámide
    objects.append(Pyramid(28,-28, color=(0.9,0.75,0.1),color2=(0.8,0.6,0.05), speed=1.0))

    print(f"[Ciudad 3D] {len(objects)} objetos creados")
    return objects


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    # Hilo de cámara
    t = threading.Thread(target=hand_thread, daemon=True)
    t.start()

    pygame.init()
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL | RESIZABLE)
    pygame.display.set_caption("Ciudad 3D – Control por Manos")

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(60, WIDTH/HEIGHT, 0.5, 400)
    glMatrixMode(GL_MODELVIEW)

    glEnable(GL_LIGHTING); glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, [10,30,10,1])
    glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1,1,0.9,1])
    glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.3,0.3,0.35,1])
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    city  = build_city()
    clock = pygame.time.Clock()

    roads = [
        (-55,0,55,0),   (0,-55,0,55),
        (-55,10,55,10), (-55,-10,55,-10),
        (10,-55,10,55), (-10,-55,-10,55),
    ]

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == QUIT: running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE: running = False
                with cam_lock:
                    if event.key == K_LEFT:  cam_state["angle_h"] -= 5
                    if event.key == K_RIGHT: cam_state["angle_h"] += 5
                    if event.key == K_UP:    cam_state["angle_v"] = min(85,cam_state["angle_v"]-3)
                    if event.key == K_DOWN:  cam_state["angle_v"] = max(5, cam_state["angle_v"]+3)
                    if event.key in (K_PLUS,K_EQUALS):
                        cam_state["distance"] = max(10,cam_state["distance"]-2)
                    if event.key == K_MINUS:
                        cam_state["distance"] = min(120,cam_state["distance"]+2)

        for obj in city:
            obj.update(dt)

        with cam_lock:
            ah   = math.radians(cam_state["angle_h"])
            av   = math.radians(cam_state["angle_v"])
            dist = cam_state["distance"]

        ex = dist*math.cos(av)*math.sin(ah)
        ey = dist*math.sin(av)
        ez = dist*math.cos(av)*math.cos(ah)

        glClearColor(0.5,0.7,1.0,1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        gluLookAt(ex,ey,ez, 0,2,0, 0,1,0)

        # Cielo (esfera grande)
        glDisable(GL_LIGHTING)
        glColor4f(0.4,0.6,0.9,1.0)
        q=gluNewQuadric(); gluSphere(q,150,24,24); gluDeleteQuadric(q)
        glEnable(GL_LIGHTING)

        draw_floor()
        for r in roads: draw_road(*r, width=3)
        for obj in city: obj.draw()

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
