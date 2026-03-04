import cv2 as cv
import numpy as np

img = np.ones((500, 500, 3), np.uint8) * 255

# Posición y velocidad del círculo
x, y = 250, 250
vx, vy = 5, 4  # velocidad en x e y
radio = 20

while True:
    # Limpiar el fondo
    img = np.ones((500, 500, 3), np.uint8) * 255

    # Mover el círculo
    x += vx
    y += vy

    # Rebotar en los bordes
    if x + radio >= 500 or x - radio <= 0:
        vx = -vx
    if y + radio >= 500 or y - radio <= 0:
        vy = -vy

    # Dibujar el círculo
    cv.circle(img, (x, y), radio, (255, 0, 0), -1)

    cv.imshow('Pong', img)

    # Salir con la tecla ESC
    if cv.waitKey(16) == 27:
        break

cv.destroyAllWindows()