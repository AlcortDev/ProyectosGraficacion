import cv2
import numpy as np

# Leer imagen (solo para generar las máscaras)
img = cv2.imread('frutas.png')
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Definición de rangos HSV por color
rangos = {
    "Rojo": [
        (np.array([0, 100, 100]), np.array([10, 255, 255])),
        (np.array([160, 100, 100]), np.array([179, 255, 255]))
    ],
    "Verde": [
        (np.array([35, 100, 100]), np.array([85, 255, 255]))
    ],
    "Amarillo": [
        (np.array([20, 100, 100]), np.array([30, 255, 255]))
    ]
}

kernel = np.ones((5, 5), np.uint8)
area_minima = 500

resultados = []

for color, rangos_color in rangos.items():

    # Generar máscara combinada por color
    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)

    for lower, upper in rangos_color:
        mask |= cv2.inRange(hsv, lower, upper)

    # Limpieza morfológica
    mask_limpia = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # Componentes conectados
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask_limpia, connectivity=8
    )

    # Filtrar por área
    areas_validas = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= area_minima:
            areas_validas.append(area)

    # Observaciones automáticas
    if len(areas_validas) == 0:
        obs = "No se detectaron regiones válidas"
    elif len(areas_validas) > 0 and min(areas_validas) < area_minima * 2:
        obs = "Presencia leve de ruido residual"
    else:
        obs = "Segmentación estable"

    resultados.append((color, len(areas_validas), obs))

# Reporte en tabla
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(" Color     Número Detectado   Observaciones")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

for r in resultados:
    print(f" {r[0]:<9} {r[1]:<17} {r[2]}")

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")