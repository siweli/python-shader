#version 330 core
in vec2 in_position;
in vec2 in_texcoord_0;  // note the attribute name from moderngl-window's quad
out vec2 v_texcoord;
void main() {
    v_texcoord = in_texcoord_0;
    gl_Position = vec4(in_position, 0.0, 1.0);
}