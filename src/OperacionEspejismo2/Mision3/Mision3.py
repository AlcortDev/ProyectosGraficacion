import cv2
import numpy as np
import math


img = np.zeros((600, 600, 3), dtype=np.uint8)
img[:] = (40, 20, 20)

# Circulo amarillo Exterior
cv2.circle(img, (300, 300), 170, (0, 255, 255), 3)

# Circulo amarillo interior
cv2.circle(img, (300, 300), 110, (0, 255, 255), 2)

# Rectangulo rojo relleno
cv2.rectangle(img, (250, 260), (350, 340), (0, 0, 255), -1)

#Diagonales blancas
cv2.line(img, (0, 0), (600, 600), (255, 255, 255), 2)
cv2.line(img, (600, 0), (0, 600), (255, 255, 255), 2)

#Circulos verdes
centro_x, centro_y = 300, 300
radio = 140

for i in range(8):
    angulo = i * (2 * math.pi / 8)  # dividir el círculo en 8 partes
    
    x = int(centro_x + radio * math.cos(angulo))
    y = int(centro_y + radio * math.sin(angulo))
    
    cv2.circle(img, (x, y), 8, (0, 255, 0), -1)

#Texto
texto = "SECTOR-9"
fuente = cv2.FONT_HERSHEY_SIMPLEX
escala = 1
grosor = 2

# Obtener tamaño del texto para centrarlo
(tw, th), _ = cv2.getTextSize(texto, fuente, escala, grosor)

x_texto = (600 - tw) // 2
y_texto = 560

cv2.putText(img, texto, (x_texto, y_texto), fuente, escala, (255, 255, 255), grosor)

#Guardar imagen
cv2.imwrite(r"C:\Users\Alvaro\Documents\Escuela\Sexto\Graficacion\Entorno\grafi3.12\src\OperacionEspejismo2\Mision3\m3_sello_forjado_v2.png", img)

# Mostrar (opcional)
cv2.imshow("Sello", img)
cv2.waitKey(0)
cv2.destroyAllWindows()