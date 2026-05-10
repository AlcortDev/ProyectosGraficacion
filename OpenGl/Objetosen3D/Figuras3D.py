import sys
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# Variables globales
rotation_angle = 0.0
window_width = 1600
window_height = 900

def draw_sphere():
    glColor3f(1.0, 0.2, 0.2)
    quadric = gluNewQuadric()
    gluSphere(quadric, 0.5, 32, 32) # Aumenté los segmentos para que se vea redonda
    gluDeleteQuadric(quadric)

def draw_cube():
    glColor3f(0.2, 1.0, 0.2)
    glutSolidCube(0.8)

def draw_cone():
    glColor3f(0.2, 0.2, 1.0)
    quadric = gluNewQuadric()
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quadric, 0.5, 0.0, 1.0, 32, 32)
    gluDeleteQuadric(quadric)

def draw_torus():
    glColor3f(1.0, 1.0, 0.2)
    glutSolidTorus(0.2, 0.5, 32, 32)

def draw_teapot():
    glColor3f(1.0, 0.2, 1.0)
    glutSolidTeapot(0.5)

def draw_cylinder():
    glColor3f(0.2, 1.0, 1.0)
    quadric = gluNewQuadric()
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quadric, 0.4, 0.4, 1.0, 32, 32)
    gluDeleteQuadric(quadric)

def draw_disk():
    glColor3f(1.0, 0.5, 0.2)
    quadric = gluNewQuadric()
    gluDisk(quadric, 0.2, 0.6, 32, 32)
    gluDeleteQuadric(quadric)

def draw_dodecahedron():
    glColor3f(0.5, 1.0, 0.5)
    glScalef(0.4, 0.4, 0.4) # Escalado porque es muy grande por defecto
    glutSolidDodecahedron()

def draw_octahedron():
    glColor3f(1.0, 0.5, 0.5)
    glutSolidOctahedron()

def draw_tetrahedron():
    glColor3f(0.5, 0.5, 1.0)
    glutSolidTetrahedron()

def draw_icosahedron():
    glColor3f(1.0, 1.0, 0.5)
    glutSolidIcosahedron()

def draw_partial_disk():
    glColor3f(0.8, 0.3, 0.8)
    quadric = gluNewQuadric()
    gluPartialDisk(quadric, 0.2, 0.6, 32, 16, 0, 270)
    gluDeleteQuadric(quadric)

def setup_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    light_position = [2.0, 2.0, 2.0, 1.0]
    light_ambient = [0.3, 0.3, 0.3, 1.0]
    light_diffuse = [1.0, 1.0, 1.0, 1.0]
    light_specular = [1.0, 1.0, 1.0, 1.0]
    
    glLightfv(GL_LIGHT0, GL_POSITION, light_position)
    glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
    glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)

def draw_all_3d_shapes():
    global rotation_angle, window_width, window_height
    
    shapes = [
        draw_sphere, draw_cube, draw_cone, draw_torus,
        draw_teapot, draw_cylinder, draw_disk, draw_dodecahedron,
        draw_octahedron, draw_tetrahedron, draw_icosahedron, draw_partial_disk
    ]
    
    cols = 4
    rows = 3
    
    for idx, draw_func in enumerate(shapes):
        col = idx % cols
        row = idx // cols
        
        # Configurar viewport para cada celda
        cell_width = window_width // cols
        cell_height = window_height // rows
        x = col * cell_width
        y = window_height - (row + 1) * cell_height
        
        glViewport(x, y, cell_width, cell_height)
        
        # Proyección
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        # Evitar división por cero
        aspect = cell_width / cell_height if cell_height > 0 else 1.0
        gluPerspective(45, aspect, 0.1, 50.0)
        
        # Vista
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0, 0, 3, 0, 0, 0, 0, 1, 0)
        
        # Rotación animada
        glRotatef(rotation_angle, 0, 1, 0)   hbgvcx
        glRotatef(rotation_angle * 0.5, 1, 0, 0)
        
        glPushMatrix()
        draw_func()
        glPopMatrix()

def display():
    """Callback de dibujado de GLUT"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    draw_all_3d_shapes()
    glutSwapBuffers()

def idle():
    """Callback de actualización (animación)"""
    global rotation_angle
    rotation_angle += 0.5
    if rotation_angle > 360:
        rotation_angle -= 360
    glutPostRedisplay() # Obliga a redibujar el frame

def reshape(w, h):
    """Callback para manejar el cambio de tamaño de la ventana"""
    global window_width, window_height
    window_width = w
    window_height = h

def main():
    # 1. Inicializar GLUT correctamente con los argumentos del sistema
    glutInit(sys.argv)
    
    # 2. Configurar modo de visualización (doble buffer, RGB, Profundidad y Multimuestreo para anti-aliasing)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    
    # 3. Crear ventana
    glutInitWindowSize(window_width, window_height)
    glutCreateWindow(b"Todas las Figuras 3D de OpenGL (Pure GLUT)")
    
    # 4. Configurar OpenGL
    glClearColor(0.1, 0.1, 0.15, 1.0)
    setup_lighting()
    #glEnable(GL_MULTISAMPLE)
    glShadeModel(GL_SMOOTH)
    
    # 5. Registrar Callbacks
    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutReshapeFunc(reshape)
    
    # 6. Iniciar el loop de GLUT
    glutMainLoop()

if __name__ == "__main__":
    main()
