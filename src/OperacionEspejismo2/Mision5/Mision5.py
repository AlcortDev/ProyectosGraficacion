import cv2
import numpy as np

#  GENERAR IMAGEN CON RUIDO
alto, ancho = 300, 700

# Ruido aleatorio en BGR
img = np.random.randint(0, 256, (alto, ancho, 3), dtype=np.uint8)

#  TEXTO "TRAMPOSO"
texto = "CLAVE-DELTA9"
fuente = cv2.FONT_HERSHEY_SIMPLEX

color_trampa = (10, 255, 10)  # (B, G, R)

cv2.putText(img, texto, (50, 180), fuente, 2, color_trampa, 4)

# Guardar evidencia
cv2.imwrite("m5_tricolor.png", img)

#  SEPARAR CANALES
b, g, r = cv2.split(img)

#  PROBAR RECUPERACIONES

# Diferencia G - B
diff_gb = cv2.absdiff(g, b)

# (Opcional) normalizar para mejorar contraste
diff_gb = cv2.normalize(diff_gb, None, 0, 255, cv2.NORM_MINMAX)

#  UMBRALIZAR (hacer visible texto)
_, mask = cv2.threshold(diff_gb, 50, 255, cv2.THRESH_BINARY)

# GUARDAR RESULTADO FINAL
cv2.imwrite("m5_mensaje.png", mask)

# Mostrar (opcional)
cv2.imshow("Original", img)
cv2.imshow("Canal G", g)
cv2.imshow("Recuperado", mask)
cv2.waitKey(0)
cv2.destroyAllWindows()