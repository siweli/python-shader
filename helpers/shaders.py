import sys
import ctypes
import numpy as np
import dxcam
import OpenGL.GL as gl

from PyQt5.QtWidgets import QApplication, QMainWindow, QOpenGLWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QSurfaceFormat, QGuiApplication


VERTEX_SHADER_SOURCE = """
#version 330 core
layout (location = 0) in vec2 position;
layout (location = 1) in vec2 texCoord;
out vec2 TexCoord;
void main() {
    TexCoord = texCoord;
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

FRAGMENT_SHADER_SOURCE = """
#version 330 core
in vec2 TexCoord;
out vec4 FragColor;
uniform sampler2D screenTexture;
void main() {
    vec4 color = texture(screenTexture, TexCoord);
    // If the pixel is mostly red, output green; adjust thresholds as needed.
    if(color.r > 0.6 && color.g < 0.4 && color.b < 0.4)
        FragColor = vec4(0.0, 1.0, 0.0, 1.0);
    else
        FragColor = color;
}
"""




def compile_shader(source, shader_type):
    shader = gl.glCreateShader(shader_type)
    gl.glShaderSource(shader, source)
    gl.glCompileShader(shader)
    status = gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS)
    if not status:
        error = gl.glGetShaderInfoLog(shader)
        raise RuntimeError("Shader compilation failed: " + error.decode())
    return shader



def create_program(vertex_src, fragment_src):
    vertex_shader = compile_shader(vertex_src, gl.GL_VERTEX_SHADER)
    fragment_shader = compile_shader(fragment_src, gl.GL_FRAGMENT_SHADER)
    program = gl.glCreateProgram()
    gl.glAttachShader(program, vertex_shader)
    gl.glAttachShader(program, fragment_shader)
    gl.glLinkProgram(program)
    status = gl.glGetProgramiv(program, gl.GL_LINK_STATUS)
    if not status:
        error = gl.glGetProgramInfoLog(program)
        raise RuntimeError("Program linking failed: " + error.decode())
    gl.glDeleteShader(vertex_shader)
    gl.glDeleteShader(fragment_shader)
    return program




class OverlayGLWidget(QOpenGLWidget):
    def __init__(self, parent=None, fps=30):
        super().__init__(parent)

        # calculate ms between frames based on inputted fps
        timer_interval = int(1000 / fps) # we do this as msec must be an integer

        # set up timer and other vars
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(timer_interval)
        self.program = None
        self.vao = None
        self.vbo = None
        self.texture_id = None
        self.camera = None  # We'll initialize dxcam below.

    def initializeGL(self):
        # Set clear color to transparent.
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        self.program = create_program(VERTEX_SHADER_SOURCE, FRAGMENT_SHADER_SOURCE)
        gl.glUseProgram(self.program)

        # Define a fullscreen quad (NDC coordinates).
        # Each vertex: (position.x, position.y, texCoord.x, texCoord.y)
        vertices = np.array([
            -1.0, -1.0,  0.0, 0.0,
             1.0, -1.0,  1.0, 0.0,
             1.0,  1.0,  1.0, 1.0,
            -1.0,  1.0,  0.0, 1.0,
        ], dtype=np.float32)
        
        # Create VBO.
        self.vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)
        
        # Create VAO.
        self.vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.vao)
        # Position attribute.
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 4 * 4, gl.ctypes.c_void_p(0))
        # TexCoord attribute.
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, False, 4 * 4, gl.ctypes.c_void_p(2 * 4))
        gl.glBindVertexArray(0)
        
        # Generate texture for the captured desktop.
        self.texture_id = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        
        # Determine the primary monitor region.
        primary = QGuiApplication.primaryScreen().geometry()
        region = (primary.x(), primary.y(), primary.width(), primary.height())
        
        # Create and start the dxcam camera.
        self.camera = dxcam.create(device_idx=0, region=region, output_color="BGR")
        self.camera.start()

    def paintGL(self):
        # Get the latest frame from dxcam.
        frame = self.camera.get_latest_frame()
        if frame is None:
            return  # No new frame yet.
        if frame.shape[2] == 4:
            frame = frame[..., :3]  # Drop alpha if present.
        # dxcam returns BGR; convert to RGB.
        img = frame[..., ::-1]
        # Flip vertically so the image orientation matches the desktop.
        img = np.flipud(img)
        height, width, _ = img.shape

        # Update texture with captured image.
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, width, height,
                        0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, img)

        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glUseProgram(self.program)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
        loc = gl.glGetUniformLocation(self.program, "screenTexture")
        gl.glUniform1i(loc, 0)
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_FAN, 0, 4)
        gl.glBindVertexArray(0)

    def resizeGL(self, width, height):
        gl.glViewport(0, 0, width, height)