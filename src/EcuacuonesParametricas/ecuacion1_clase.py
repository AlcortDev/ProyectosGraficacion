import numpy as np
import cv2


# Definir los parámetros iniciales
width, height = 1000, 1000  # Ampliar la ventana para ver toda la figura
img = np.ones((height, width, 3), dtype=np.uint8)*255

# Parámetros de la curva de Limacon
a, b = 50, 50  # Reducir los valores de a y b para que la curva se ajuste mejor
theta_increment = 0.1 # Incremento del ángulo
max_theta = 2 * np.pi  # Un ciclo completo

a, b = 50, 50  # Reducir los valores de a y b para que la curva se ajuste mejor  
theta_increment = 0.1 # Incremento del ángulo
max_theta = 2 * np.pi

# Constante de multiplicación del ángulo 
k1 = 0.25 
k2 = 1.7 
k3 = 2.5
k4 = 3

# Centro de la imagen 1
center_x1, center_y1 = width // 5, height // 5

# Centro de la imagen 2
center_x2, center_y2 = width // 6, (3 * height) // 6

# Centro de la imagen 3
center_x3, center_y3 = 3 * width // 4, height // 2

# Centro de la imagen 4
center_x4, center_y4 = (width * 4) // 5, height // 5


theta = 0  # Ángulo inicial

while True:  # Bucle infinito
    # Limpiar la imagen
    #img = np.ones((width, height, 3), dtype=np.uint8) * 255
    
    # Dibujar la curva completa desde 0 hasta theta
    for t in np.arange(0, theta, theta_increment):
        # Calcular las coordenadas paramétricas (x, y) para la curva de Limacon
        r = a + b * np.cos(k1 * t)
        x = int(center_x1 + r * np.cos(t))
        y = int(center_y1 + r * np.sin(t))
        
        # Dibujar un círculo en la posición calculada
        #cv2.circle(img, (x, y), 3, (0, 234, 0), -1)  # Color rojo
        cv2.circle(img, (x-2, y-2), 3, (0, 0, 0), -1)  # Color rojo
    

   
    if cv2.waitKey(30) & 0xFF == 27:  # Esperar 30ms, salir con 'ESC'
        break

    # Dibujar la curva completa desde 0 hasta theta
    for t in np.arange(0, theta, theta_increment):
        # Calcular las coordenadas paramétricas (x, y) para la curva de Limacon
        r = a + b * np.cos(k2 * t)
        x = int(center_x2 + r * np.cos(t))
        y = int(center_y2 + r * np.sin(t))
        
        # Dibujar un círculo en la posición calculada
        #cv2.circle(img, (x, y), 3, (0, 234, 0), -1)  # Color rojo
        cv2.circle(img, (x-2, y-2), 3, (0, 110, 100), -1)  # Color rojo
    

   
    if cv2.waitKey(30) & 0xFF == 27:  # Esperar 30ms, salir con 'ESC'
        break

    # Dibujar la curva completa desde 0 hasta theta
    for t in np.arange(1, theta, theta_increment):
        # Calcular las coordenadas paramétricas (x, y) para la curva de Limacon
        r = a + b * np.cos(k3 * t)
        x = int(center_x3 + r * np.cos(t))
        y = int(center_y3 + r * np.sin(t))
        
        # Dibujar un círculo en la posición calculada
        #cv2.circle(img, (x, y), 3, (0, 234, 0), -1)  # Color rojo
        cv2.circle(img, (x-2, y-2), 3, (0, 30, 150), 1)  # Color rojo
    
    for t in np.arange(1, theta, theta_increment):
        # Calcular las coordenadas paramétricas (x, y) para la curva de Limacon
        r = a + b * np.cos(k4 * t)
        x = int(center_x4 + r * np.cos(t))
        y = int(center_y4 + r * np.sin(t))
        
        # Dibujar un círculo en la posición calculada
        #cv2.circle(img, (x, y), 3, (0, 234, 0), -1)  # Color rojo
        cv2.circle(img, (x-2, y-2), 3, (0, 50, 150), 1)  # Color rojo
    
    # Mostrar la imagen
    cv2.imshow("Parametric Animation", img)
    #img = np.ones((width, height, 3), dtype=np.uint8) * 255
    
    # Incrementar el ángulo
    theta += theta_increment
    
    # Reiniciar theta si alcanza su valor máximo
    #if theta >= max_theta:
    #    theta = 0  # Reinicia la animación para que se repita

    # Pausar para ver la animación
    if cv2.waitKey(30) & 0xFF == 27:  # Esperar 30ms, salir con 'ESC'
        break
# Cerrar la ventana al finalizar
cv2.destroyAllWindows()