#Alvaro Jesús Cortés Valencia

import cv2 as cv
import numpy as np

ancho = 500
largo = 500
canvas = np.ones([largo,ancho], np.uint8)*255



def dibujar_linea(iniciox, finalx,inicioy,finaly):
    
    for i in range (iniciox*10, finalx*10):
        for j in range(inicioy*10, finaly*10):
            canvas[j,i] = 0
            
            
        


dibujar_linea(22,31,25,26)

dibujar_linea(20,22,26,27)
dibujar_linea(31,33,26,27)

dibujar_linea(19,20,27,29)
dibujar_linea(33,34,27,29)

dibujar_linea(18,19,29,33)
dibujar_linea(34,35,29,33)

#ojo izquierdo
dibujar_linea(21, 24,32, 33 )

#Nariz
dibujar_linea(26,27, 32, 33)
dibujar_linea(25,28, 33, 34)

#ojo derecho
dibujar_linea( 29, 32, 30, 33)

#Sonrisa
dibujar_linea(31, 32, 34, 36)
dibujar_linea(21, 22, 34, 36)

dibujar_linea(22, 31, 35, 36)

#Dientes
dibujar_linea(22, 23, 36, 37)
dibujar_linea(24, 25, 36, 37)
dibujar_linea(26, 27, 36, 37)
dibujar_linea(28, 29, 36, 37)
dibujar_linea(30, 31, 36, 37)

dibujar_linea(23, 30, 37, 38)

#mejillas
dibujar_linea(19, 20, 33, 35)
dibujar_linea(33, 34, 33, 35)

#mandibula 
dibujar_linea(18, 19,34,37 )
dibujar_linea(34, 35,34,37 )

dibujar_linea(19, 21, 37, 39)
dibujar_linea(32, 34, 37, 39)

dibujar_linea(21, 23,38,39 )
dibujar_linea(30, 32,38,39 )

dibujar_linea(23, 30, 39, 40)





cv.imshow("Imagen perrona", canvas)
cv.waitKey(0)
cv.destroyAllWindows()