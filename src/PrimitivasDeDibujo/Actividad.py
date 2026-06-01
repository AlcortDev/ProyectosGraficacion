import cv2 as cv
import numpy as np 

img = np.ones((500,500,3), np.uint8)*255
##creamos una figura simple y sólida con -1. si quitamos -1 tendremos solo el marco
cv.rectangle(img, (10,10), (200,100), (220,56,100), 1)
#cv.rectangle(img, (20,20), (210,110), (220,56,50), 3 )
#
#cv.circle(img, (255,255), 40, (23, 43, 144), -1 )
#cv.circle(img, (255,255), 20, (0,0 , 255), -1 )
#
#
#cv.line(img, (255,255), (100,50), (23, 244, 144), 4)




for i in range(3000):
    
    borde = i
    if borde >= 500:
        cv.circle(img, (i,), 20 , (255, 0, 0), -1 )
        cv.imshow('img', img)
        img = np.ones((500,500,3), np.uint8)*150 
        cv.waitKey(1)
 






cv.imshow('img', img)
cv.waitKey(0)
cv.destroyAllWindows()
