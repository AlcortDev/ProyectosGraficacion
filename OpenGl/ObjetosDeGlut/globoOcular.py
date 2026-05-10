import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

def draw_eye():
    # Globo ocular
    glColor3f(1.0, 1.0, 1.0)
    glutSolidSphere(1.0, 50, 50)

    # Iris (azul)
    glColor3f(0.3, 0.5, 0.9)
    glPushMatrix()
    glTranslatef(0, 0, 0.57)
    glutSolidSphere(0.2, 30, 30)
    glPopMatrix()

    # Pupila (negra)
    glColor3f(0.0, 0.0, 0.0)
    glPushMatrix()
    glTranslatef(0, 0, 1.02)
    glutSolidSphere(0.2, 20, 20)
    glPopMatrix()

    # Nervio óptico
    glColor3f(1.0, 0.6, 0.6)
    glPushMatrix()
    glTranslatef(0, 0, -1.0)
    glRotatef(-90, 1, 0, 0)
    quad = gluNewQuadric()
    gluCylinder(quad, 0.15, 0.05, 0.6, 20, 20)
    glPopMatrix()

def main():
    if not glfw.init():
        return
    window = glfw.create_window(800, 600, "Ojo 3D con OpenGL", None, None)
    if not window:
        glfw.terminate()
        return
    glfw.make_context_current(window)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)

    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, 800 / 600, 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)

    while not glfw.window_should_close(window):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        gluLookAt(3, 1.5, 3, 0, 0, 0, 0, 1, 0)

        draw_eye()

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    glutInit()
    main()