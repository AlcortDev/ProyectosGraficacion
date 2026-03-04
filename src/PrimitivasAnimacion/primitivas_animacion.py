import numpy as np
import cv2 as cv

# Lienzo blanco
img = np.ones((500, 500, 3), np.uint8)*255

# Cara (círculo grande)
cv.circle(img, (200, 200), 120, (0, 255, 255), -1)  # Amarillo relleno

# Ojos
cv.circle(img, (160, 170), 20, (0, 0, 0), -1)
cv.circle(img, (240, 170), 20, (0, 0, 0), -1)

 #Boca (media elipse)
cv.ellipse(img, (200, 230), (60, 40), 0, 0, 180, (0, 0, 0), 4)

for i in range (20):
    cv.ellipse(img, (200, 230-i), (60, 40), 0, 0, 180, (0, 0, 0), 4)
    cv.imshow('Carita', img)
    cv.waitKey(70)

for i in range (20):
    cv.ellipse(img, (200, 275+i), (100, 120), 20, 50, 50, (30, 20, 150), 30)
    cv.imshow('Carita', img)
    cv.waitKey(70)
cv.imshow('Carita', img)
cv.waitKey(0)
cv.destroyAllWindows()