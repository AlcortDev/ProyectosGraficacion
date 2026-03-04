import cv2 as cv


img = cv.imread('tu_imagen.jpg', 0)
cv.imshow('salida', img)
x,y=img.shape
for i in range(x):
        for j in range(y):
                img[i,j]=255-img[i,j]
cv.imshow('negativo', img)
print( img.shape, x , y)
cv.waitKey(0)
cv.destroyAllWindows()