import numpy as np
import cv2 as cv

rostro = cv.CascadeClassifier(r'C:\Users\Alvaro\Documents\Escuela\Sexto\Graficacion\Entorno\grafi3.12\src\hardCascades\haarcascade_frontalface_alt2.xml')
cap = cv.VideoCapture(0)
x=y=w=h= 0 

count = 0
while True:
    ret, frame = cap.read()
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    rostros = rostro.detectMultiScale(gray, 1.3, 5)
    for(x, y, w, h) in rostros:
        m1 = int(h/2)
        n1 = int(w/2)
        frame = cv.rectangle(frame, (x,y), (x+w, y+h), (0, 255, 0), 2)
        frame = cv.circle(frame, (x+n1,y+m1), int(w/2) , (255, 0 ,0), 2 )
        #img = frame[y:y+h,x:x+w]
        #count = count + 1   
    
    #name = '/home/likcos/imgs/cara'+str(count)+'.jpg'
    #cv.imwrite(name, frame)
    cv.imshow('rostros', frame)
    #cv.imshow('cara', img)
    
    k = cv.waitKey(1)
    if k == 27:
        break
cap.release()
cv.destroyAllWindows()