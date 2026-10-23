shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, shadows_disabled, unshaded;
uniform vec4 foam_color : source_color = vec4(.91,.99,.97,1.0);
uniform vec3 lighting_color : source_color = vec3(1.0);
uniform float lighting_energy = 1.0;
uniform float foam_coverage = .63;
uniform float foam_speed = .16;
uniform float foam_irregularity = .65;
uniform bool animation_enabled = true;
varying vec3 world_position;
void vertex() { world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
void fragment() {
 float clock=animation_enabled ? TIME*foam_speed : 0.0;
 float along=world_position.x+world_position.z;
 float n=.5+.26*sin(along*8.7+clock)+.15*sin(along*19.3-clock*.8)+.09*sin(along*37.1+clock*.3);
 float broken=smoothstep(1.0-foam_coverage,1.08-foam_coverage,n);
 float width=.35+.35*n*foam_irregularity;
 float across=1.0-smoothstep(width,width+.24,UV.y);
 float tip=smoothstep(0.0,.15,UV.y);
 ALBEDO=foam_color.rgb*lighting_color*lighting_energy;
 ROUGHNESS=.95;
 ALPHA=broken*across*tip*(.72+.2*n)*COLOR.a;
}
