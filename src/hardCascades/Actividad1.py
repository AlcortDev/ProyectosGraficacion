import cv2 as cv 

rostro = cv.CascadeClassifier(r'C:\Users\Alvaro\Documents\Escuela\Sexto\Graficacion\Entorno\grafi3.12\src\hardCascades\haarcascade_frontalface_alt2.xml')
cap = cv.VideoCapture(0)


while True:
    ret, img = cap.read()
    if not ret:
        break
        
    gris = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    rostros = rostro.detectMultiScale(gris, 1.3, 5)

    for(x,y,w,h) in rostros:

        img = cv.rectangle(img, (x,y), (x+w, y+h), (234,23,23), 3)

        # OJOS
        img = cv.circle(img, (x + int(w*0.3), y + int(h*0.4)), 21, (0,0,0), 2)
        img = cv.circle(img, (x + int(w*0.7), y + int(h*0.4)), 21, (0,0,0), 2)
        img = cv.circle(img, (x + int(w*0.3), y + int(h*0.4)), 20, (255,255,255), -1)
        img = cv.circle(img, (x + int(w*0.7), y + int(h*0.4)), 20, (255,255,255), -1)
        img = cv.circle(img, (x + int(w*0.3), y + int(h*0.4)), 5, (0,0,255), -1)
        img = cv.circle(img, (x + int(w*0.7), y + int(h*0.4)), 5, (0,0,255), -1)

        # OREJAS
        img = cv.circle(img, (x - int(w*0.1), y + int(h*0.5)), int(w*0.15), (0,255,255), 3)
        img = cv.circle(img, (x + w + int(w*0.1), y + int(h*0.5)), int(w*0.15), (0,255,255), 3)

        # BOCA
        img = cv.ellipse(
            img,
            (x + int(w*0.5), y + int(h*0.75)),
            (int(w*0.25), int(h*0.1)),
            0,
            0,
            180,
            (0,0,255),
            3
        )

        # BIGOTE
        img = cv.line(
            img,
            (x + int(w*0.35), y + int(h*0.65)),
            (x + int(w*0.65), y + int(h*0.65)),
            (0,0,0),
            4
        )

        img2 = img[y:y+h, x:x+w]
        cv.imshow('img2', img2)

    cv.imshow('img', img)

    if cv.waitKey(1) == ord('q'):
        break

cap.release()
cv.destroyAllWindows()