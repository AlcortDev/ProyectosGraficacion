import cv2
import numpy as np
from pathlib import Path

OUT = Path("/home/likcos/Scripts/marcador_aruco_id0.png")
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
if hasattr(cv2.aruco, "generateImageMarker"):
    img = cv2.aruco.generateImageMarker(dictionary, 0, 400)
else:
    img = cv2.aruco.drawMarker(dictionary, 0, 400)
border = 40
canvas = np.full((480, 480), 255, np.uint8)
canvas[40:440, 40:440] = img
cv2.imwrite(str(OUT), canvas)
print("OK ->", OUT)