## Practica 1 || Uso de openCv para crear una imagen usando "puntos"

### Pocedimiento
En esta práctica utilizamos OpenCv y Numpy para la creación de una imagen simple de 8-bits

### Ejecucion
El metodo que utilicé se basa en coordenadas.

creé una función que recibe 4 coordenadas

funcion (cordenada de inicio en x, coordenada de fin en x, coordenada de inicio en y, coordenada de inicio en y)

la función de crear lineas creando puntos de 10x10 pixeles, toma las coordenadas en x & y para definir que cuadrantes de la matriz deben de cambiar de color.


me di cuenta de que a pesar de que este control es muy preciso, tiene la desventaja de que es todo manual, al hacer dibujos más grandes o complicados, será muy tardado además de ser dificil de mantener una estructura ordenada con la cual podamos tener nocion de qué hace cada linea.

Sin embargo, considero que es un enfoque eficiente, y con posibilidades de ser escalado

