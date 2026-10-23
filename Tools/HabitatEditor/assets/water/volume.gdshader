shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_back;

uniform vec4 shallow_color : source_color = vec4(.21,.70,.72,1.0);
uniform vec4 deep_color : source_color = vec4(.055,.28,.43,1.0);
uniform float opacity = .32;
uniform float side_opacity = .29;
uniform float depth_strength = .32;
uniform float roughness_value = .48;
uniform float highlight_strength = .12;
uniform float ripple_speed = .3;
uniform float ripple_strength = .025;
uniform float ripple_scale = 2.1;
uniform bool animation_enabled = true;
varying vec3 world_position;
varying vec3 world_normal;

void vertex() {
 world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;
 world_normal=normalize(MODEL_NORMAL_MATRIX*NORMAL);
}
void fragment() {
 float clock=animation_enabled ? TIME*ripple_speed : 0.0;
 vec2 p=world_position.xz*ripple_scale;
 float wave=sin(p.x*1.7+p.y*.8+clock)+sin(p.y*2.3-p.x*.5-clock*.7);
 float depth_mix=1.0-exp(-max(UV2.x,0.0)*depth_strength);
 // UV2.x is contiguous-column depth, UV2.y is distance below that column's top.
 float tint=clamp(depth_mix*.6+(1.0-exp(-UV2.y*depth_strength))*.45,0.0,.9);
 vec3 base=mix(shallow_color.rgb,deep_color.rgb,tint);
 float surface=smoothstep(.5,.9,world_normal.y);
 float streak=pow(max(0.0,sin(p.x*.7+p.y*1.2+wave*.35+clock*.4)),28.0);
 ALBEDO=base+vec3(wave*ripple_strength*.15)+vec3(.70,.88,.88)*streak*highlight_strength*surface;
 ROUGHNESS=roughness_value;
 SPECULAR=.16;
 METALLIC=0.0;
 ALPHA=clamp(mix(side_opacity,opacity,surface)+depth_mix*.10,0.02,.85);
}
