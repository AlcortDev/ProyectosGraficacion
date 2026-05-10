import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math

# Variable global para rotación
rotation_angle = 0.0

def draw_sphere():
    """Esfera usando GLU"""
    glColor3f(1.0, 0.2, 0.2)
    quadric = gluNewQuadric()
    gluSphere(quadric, 0.5, 32, 32)
    gluDeleteQuadric(quadric)

def draw_cube():
    """Cubo usando GLUT"""
    glColor3f(0.2, 1.0, 0.2)
    glutSolidCube(0.8)

def draw_cone():
    """Cono usando GLU"""
    glColor3f(0.2, 0.2, 1.0)
    quadric = gluNewQuadric()
    glRotatef(-90, 1, 0, 0)  # Orientar hacia arriba
    gluCylinder(quadric, 0.5, 0.0, 1.0, 32, 32)
    gluDeleteQuadric(quadric)

def draw_torus():
    """Toroide/Toro usando GLUT"""
    glColor3f(1.0, 1.0, 0.2)
    glutSolidTorus(0.2, 0.5, 32, 32)

def draw_teapot():
    """La famosa Tetera de Utah"""
    glColor3f(1.0, 0.2, 1.0)
    glutSolidTeapot(0.5)

def draw_cylinder():
    """Cilindro usando GLU"""
    glColor3f(0.2, 1.0, 1.0)
    quadric = gluNewQuadric()
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quadric, 0.4, 0.4, 1.0, 32, 32)
    gluDeleteQuadric(quadric)

def draw_disk():
    """Disco usando GLU"""
    glColor3f(1.0, 0.5, 0.2)
    quadric = gluNewQuadric()
    gluDisk(quadric, 0.2, 0.6, 32, 32)
    gluDeleteQuadric(quadric)

def draw_dodecahedron():
    """Dodecaedro (12 caras pentagonales)"""
    glColor3f(0.5, 1.0, 0.5)
    glutSolidDodecahedron()

def draw_octahedron():
    """Octaedro (8 caras triangulares)"""
    glColor3f(1.0, 0.5, 0.5)
    glutSolidOctahedron()

def draw_tetrahedron():
    """Tetraedro (4 caras triangulares)"""
    glColor3f(0.5, 0.5, 1.0)
    glutSolidTetrahedron()

def draw_icosahedron():
    """Icosaedro (20 caras triangulares)"""
    glColor3f(1.0, 1.0, 0.5)
    glutSolidIcosahedron()

def draw_partial_disk():
    """Disco parcial (sector circular)"""
    glColor3f(0.8, 0.3, 0.8)
    quadric = gluNewQuadric()
    gluPartialDisk(quadric, 0.2, 0.6, 32, 16, 0, 270)
    gluDeleteQuadric(quadric)

def draw_grid():
    """Dibuja una rejilla de referencia"""
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_LINES)
    for i in range(-5, 6):
        glVertex3f(i, -5, 0)
        glVertex3f(i, 5, 0)
        glVertex3f(-5, i, 0)
        glVertex3f(5, i, 0)
    glEnd()

def setup_lighting():
    """Configura iluminación para ver mejor las figuras 3D"""
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    # Luz posicional
    light_position = [2.0, 2.0, 2.0, 1.0]
    light_ambient = [0.3, 0.3, 0.3, 1.0]
    light_diffuse = [1.0, 1.0, 1.0, 1.0]
    light_specular = [1.0, 1.0, 1.0, 1.0]
    
    glLightfv(GL_LIGHT0, GL_POSITION, light_position)
    glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
    glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)

def draw_all_3d_shapes():
    """Dibuja todas las figuras 3D en una cuadrícula 4x3"""
    global rotation_angle
    
    shapes = [
        ("Esfera", draw_sphere),
        ("Cubo", draw_cube),
        ("Cono", draw_cone),
        ("Toroide", draw_torus),
        ("Tetera", draw_teapot),
        ("Cilindro", draw_cylinder),
        ("Disco", draw_disk),
        ("Dodecaedro", draw_dodecahedron),
        ("Octaedro", draw_octahedron),
        ("Tetraedro", draw_tetrahedron),
        ("Icosaedro", draw_icosahedron),
        ("Disco Parcial", draw_partial_disk),
    ]
    
    cols = 4
    rows = 3
    
    width, height = glfw.get_window_size(glfw.get_current_context())
    
    for idx, (name, draw_func) in enumerate(shapes):
        col = idx % cols
        row = idx // cols
        
        # Configurar viewport
        cell_width = width // cols
        cell_height = height // rows
        x = col * cell_width
        y = height - (row + 1) * cell_height
        
        glViewport(x, y, cell_width, cell_height)
        
        # Configurar proyección perspectiva
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, cell_width / cell_height, 0.1, 50.0)
        
        # Configurar vista
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0, 0, 3, 0, 0, 0, 0, 1, 0)
        
        # Aplicar rotación
        glRotatef(rotation_angle, 0, 1, 0)
        glRotatef(rotation_angle * 0.5, 1, 0, 0)
        
        # Dibujar la figura
        glPushMatrix()
        draw_func()
        glPopMatrix()
        
        # Dibujar el nombre (simplificado, sin texto real)
        # Para ver los nombres, necesitarías usar glutBitmapCharacter

def main():
    global rotation_angle
    
    # Inicializar GLUT (necesario para las figuras sólidas)
    glutInit()
    
    # Inicializar GLFW
    if not glfw.init():
        return

    # Crear ventana
    window = glfw.create_window(1600, 900, "Todas las Figuras 3D de OpenGL", None, None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)

    # Configurar OpenGL
    glClearColor(0.1, 0.1, 0.15, 1.0)
    setup_lighting()
    
    # Habilitar suavizado
    glEnable(GL_MULTISAMPLE)
    glShadeModel(GL_SMOOTH)

    # Bucle principal
    while not glfw.window_should_close(window):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Actualizar rotación
        rotation_angle += 0.5
        if rotation_angle > 360:
            rotation_angle -= 360
        
        draw_all_3d_shapes()
        
        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()