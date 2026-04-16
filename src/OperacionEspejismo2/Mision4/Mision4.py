import cv2
import numpy as np

# =========================
# CARGAR IMAGEN
# =========================
img = cv2.imread(r"C:\Users\Alvaro\Documents\Escuela\Sexto\Graficacion\Entorno\grafi3.12\src\OperacionEspejismo2\Mision4\m4_ruido 1.png")


# Filtro de convolucion
kernel = np.array([
    [1, 1, 1],
    [1, 1, 1],
    [1, 1, 1]
], dtype=np.float32) / 9

suavizada = cv2.filter2D(img, -1, kernel)

# Guardar (opcional)
#cv2.imwrite(r"C:\Users\Alvaro\Documents\Escuela\Sexto\Graficacion\Entorno\grafi3.12\src\OperacionEspejismo2\Mision4\m4_suavizada.png", suavizada)

#Convertir a hcv
hsv = cv2.cvtColor(suavizada, cv2.COLOR_BGR2HSV)

#Rango cyan
# Ajustable si no detecta bien
lower_cyan = np.array([80, 100, 100])
upper_cyan = np.array([100, 255, 255])

#Máscara
mask = cv2.inRange(hsv, lower_cyan, upper_cyan)

#Guardar Resultado
cv2.imwrite("m4_mask_cyan.png", mask)


cv2.imshow("Suavizada", suavizada)
cv2.imshow("Mascara Cyan", mask)
cv2.waitKey(0)
cv2.destroyAllWindows()