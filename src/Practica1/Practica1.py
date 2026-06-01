import cv2 as cv
import numpy as np

# np.ones() Genera una matriz de numeros 1

# al multiplicar por 255 encenderemos todos los pixeles de la matriz, haciendo una imagen en blanco

img = np.ones([400,400], np.uint8)*255
# Con esa linea, asignaremos en la coordenada del pixel 1,1 el valor de 0. EL valor de 0
# se refiere a la intensidad del pixel, entonces,  el pixel [1,1] estará apagado
img[1,1] = 0

for i in range(200):
    for j in range(200):
        img[i,j]= 255 - i


cv.imshow("Imagen", img)
cv.waitKey(0)
cv.destroyAllWindows()
