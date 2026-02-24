import cv2
import numpy as np

# Crear canvas de 400x400 en escala de grises (fondo blanco)
canvas = np.ones((400, 400), dtype=np.uint8) * 255

# Función para dibujar círculos con puntos
def dibujar_circulo_puntos(img, centro_x, centro_y, radio, color, grosor=2):
    """Dibuja un círculo usando puntos"""
    for angulo in np.linspace(0, 2*np.pi, 100):
        x = int(centro_x + radio * np.cos(angulo))
        y = int(centro_y + radio * np.sin(angulo))
        # Dibujar con grosor
        for i in range(-grosor, grosor+1):
            for j in range(-grosor, grosor+1):
                if 0 <= x+i < 400 and 0 <= y+j < 400:
                    img[y+j, x+i] = color

# Función para dibujar línea con puntos
def dibujar_linea_puntos(img, x1, y1, x2, y2, color, grosor=2):
    """Dibuja una línea usando puntos"""
    puntos = 50
    for t in np.linspace(0, 1, puntos):
        x = int(x1 + t * (x2 - x1))
        y = int(y1 + t * (y2 - y1))
        for i in range(-grosor, grosor+1):
            for j in range(-grosor, grosor+1):
                if 0 <= x+i < 400 and 0 <= y+j < 400:
                    img[y+j, x+i] = color

# Dibujar cara (círculo grande)
dibujar_circulo_puntos(canvas, 200, 200, 120, 0, grosor=3)

# Dibujar ojo izquierdo (círculo pequeño)
dibujar_circulo_puntos(canvas, 160, 170, 15, 0, grosor=2)
# Pupila izquierda
dibujar_circulo_puntos(canvas, 160, 170, 7, 0, grosor=4)

# Dibujar ojo derecho (círculo pequeño)
dibujar_circulo_puntos(canvas, 240, 170, 15, 0, grosor=2)
# Pupila derecha
dibujar_circulo_puntos(canvas, 240, 170, 7, 0, grosor=4)

# Dibujar nariz (línea vertical simple)
dibujar_linea_puntos(canvas, 200, 190, 200, 220, 0, grosor=2)
dibujar_linea_puntos(canvas, 200, 220, 215, 225, 0, grosor=2)

# Dibujar sonrisa (arco)
for angulo in np.linspace(np.pi/6, 5*np.pi/6, 50):
    x = int(200 + 60 * np.cos(angulo))
    y = int(230 + 60 * np.sin(angulo))
    for i in range(-2, 3):
        for j in range(-2, 3):
            if 0 <= x+i < 400 and 0 <= y+j < 400:
                canvas[y+j, x+i] = 0

# Mostrar la imagen
cv2.imshow('Caricatura con Puntos', canvas)
cv2.waitKey(0)
cv2.destroyAllWindows()