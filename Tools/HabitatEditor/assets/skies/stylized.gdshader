shader_type sky;

uniform vec3 top_color : source_color = vec3(0.15,0.52,0.70);
uniform vec3 horizon_color : source_color = vec3(0.72,0.87,0.79);
uniform vec3 lower_color : source_color = vec3(0.22,0.42,0.40);
uniform vec3 landscape_tint : source_color = vec3(0.18,0.40,0.27);
uniform vec3 cloud_color : source_color = vec3(1.0,0.96,0.88);
uniform float cloud_density = 0.4;
uniform float cloud_softness = 0.3;
uniform float cloud_phase = 0.0;
uniform float background_rotation = 0.0;
uniform bool landscape_visible = true;
uniform int landscape_kind = 0; // highlands, forest, mesas, ice
uniform float stars = 0.0;
uniform float moon = 0.0;
uniform float haze = 0.3;
uniform float horizon_offset = 0.55;

float hash3(vec3 p) { p=fract(p*vec3(.1031,.1030,.0973));p+=dot(p,p.yxz+33.33);return fract((p.x+p.y)*p.z); }
float noise3(vec3 p) {
 vec3 i=floor(p);vec3 f=fract(p);f=f*f*(3.0-2.0*f);
 return mix(mix(mix(hash3(i),hash3(i+vec3(1,0,0)),f.x),mix(hash3(i+vec3(0,1,0)),hash3(i+vec3(1,1,0)),f.x),f.y),mix(mix(hash3(i+vec3(0,0,1)),hash3(i+vec3(1,0,1)),f.x),mix(hash3(i+vec3(0,1,1)),hash3(i+vec3(1,1,1)),f.x),f.y),f.z);
}
float ridge(float a,float phase,float band) {
 float r=.045*sin(a*5.0+phase)+.030*sin(a*9.0-phase)+.018*sin(a*17.0+phase);
 if(landscape_kind==1) r+=.025*pow(abs(sin(a*73.0+phase)),3.0);
 if(landscape_kind==2) r=floor((r+.10)*22.0)/22.0-.08;
 if(landscape_kind==3) r=.10*(1.0-abs(2.0*fract(a*7.0/6.283185+phase)-1.0))+.045*(1.0-abs(2.0*fract(a*13.0/6.283185)-1.0));
 return r+band;
}
void sky() {
 vec3 d=normalize(EYEDIR);
 float h=d.y+horizon_offset;
 vec3 color=mix(horizon_color,top_color,smoothstep(-.03,.78,h));
 color=mix(color,lower_color,(1.0-smoothstep(-.85,-.10,h)));
 float angle=atan(d.z,d.x)+background_rotation;
 if(landscape_visible) {
  for(int layer=0;layer<3;layer++) {
   float index=float(layer);
   float height=ridge(angle,index*2.7,.18-index*.18);
   float mask=1.0-smoothstep(height-.004,height+.004,h);
   vec3 tint=mix(landscape_tint,horizon_color,.65-index*.20);
   tint=mix(tint,horizon_color,haze*.25);
   if(landscape_kind==3) tint=mix(tint,cloud_color,smoothstep(height-.045,height,h)*.65);
   tint=mix(tint,lower_color,(1.0-smoothstep(-.85,-.2,h))*.5);
   color=mix(color,tint,mask);
  }
 }
 // 3D noise sampled on direction: no panorama seam or finite sky dome edge.
 vec3 p=d*vec3(5.0,9.0,5.0)+vec3(cloud_phase,0.0,cloud_phase*.4);
 float n=noise3(p)*.65+noise3(p*2.1)*.25+noise3(p*4.2)*.10;
 float cloud=smoothstep(1.0-cloud_density*.85,1.0-cloud_density*.85+max(.03,cloud_softness*.35),n);
 cloud*=smoothstep(.03,.25,h)*(1.0-smoothstep(.80,1.0,h));
 color=mix(color,cloud_color,cloud*.85);
 if(stars>0.0) {
  vec3 q=d*650.0;float seed=hash3(floor(q));
  float point=pow(max(0.0,1.0-length(fract(q)-.5)*2.0),8.0);
  color+=vec3(.75,.83,1.0)*step(.985,seed)*point*stars*smoothstep(.05,.3,h);
 }
 vec3 moon_direction=normalize(vec3(cos(background_rotation-2.4)*.7,-.32,sin(background_rotation-2.4)*.7));
 float disk=smoothstep(.9990,.9995,dot(d,moon_direction));
 float halo=pow(max(0.0,dot(d,moon_direction)),140.0)*.12;
 color+=moon*(vec3(.75,.85,1.0)*disk+vec3(.25,.36,.6)*halo);
 COLOR=color;
}
