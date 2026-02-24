import cv2 as cv
img = cv.imread("src/Practica2/tu_imagen.jpg")
hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
cv.imshow('hsv', img)
cv.imshow('img', img)
cv.waitKey(0)
cv.destroyAllWindows()