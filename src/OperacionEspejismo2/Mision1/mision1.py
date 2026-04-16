import cv2 as cv
import numpy as np

img = cv.imread(r'C:\Users\Alvaro\Documents\Escuela\Sexto\Graficacion\Entorno\grafi3.12\src\OperacionEspejismo2\Mision1\m1_oscura 1.png')



img_raw = img.copy().astype(np.int32)  # int32 para evitar overflow al multiplicar

filas, columnas, canales = img_raw.shape

for y in range(filas):
    for x in range(columnas):
        for c in range(canales):
            pixel_original = img_raw[y, x, c]
            img_raw[y, x, c] = pixel_original * 50  # operador puntual inverso

# si se pasa de 255 lo regresa 
img_raw = np.clip(img_raw, 0, 255).astype(np.uint8)

cv.imwrite(r'C:\Users\Alvaro\Documents\Escuela\Sexto\Graficacion\Entorno\grafi3.12\src\OperacionEspejismo2\Mision1\m1_recuperada_raw.png', img_raw)
print("✓ Imagen guardada con modo Raw")

#Usando Numpy
img_numpy = img.astype(np.int32)       
img_numpy = np.clip(img_numpy * 50, 0, 255).astype(np.uint8)

#Usando OpenCV
# img_cv = cv2.multiply(img, np.array([50.0]))  # alternativa


# Mostrar resultado
cv.imshow('Mensaje recuperado', img_numpy)
cv.waitKey(0)
cv.destroyAllWindows()