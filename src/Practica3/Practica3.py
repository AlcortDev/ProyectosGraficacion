import cv2 as cv
import numpy as np
cap = cv.VideoCapture(0)

while(True):
    ret, img = cap.read()
    if ret:
        cv.imshow('video', img)
        img2 = cv.cvtColor(img, cv.COLOR_BGR2HSV)
        cv.imshow('video1', img2)
        
        k =cv.waitKey(1) & 0xFF
        if k == 27 :
            break
    else:
        break
   
cap.release()
cv.destroyAllWindows()