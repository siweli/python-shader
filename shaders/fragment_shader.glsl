#version 330 core
in vec2 v_texcoord;
out vec4 FragColor;

uniform sampler2D screenTexture;
uniform bool effectEnabled;

void main() {
    vec4 texColor = texture(screenTexture, v_texcoord);

    if (effectEnabled) {
        // Detect mostly green pixels and change them to red.
        if (texColor.g > 0.8 && texColor.r < 0.2 && texColor.b < 0.2) {
            FragColor = vec4(1.0, 0.0, 0.0, texColor.a);
        } else {
            FragColor = texColor;
        }
    } else {
        FragColor = texColor;
    }
}