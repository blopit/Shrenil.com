/*
 * The sky: CentrOS's "cosmic aurora", ported from the iOS app (CentrOS/Components:
 * Clouds.metal skyLayer + skyFlow, SkyCanvas.swift, SkyFilm.swift) to WebGL.
 *
 * Soft masses of coloured light on a near-black sky, as a nebula is, with the flow of
 * an aurora through them: billowed gradient noise, its coordinates bent twice (a broad
 * fold for the bulges, a finer swirl), five octaves of flow noise, ridged filaments in
 * the dense gas, one lookup towards the light for volume, and a fine faint glow far
 * back. At night light adds; by day the sky is near-white and the glows tint it.
 *
 * As in the app, the sky is baked, then made to flow: the heavy shader draws six
 * keyframes once (30 s to 60 s on the sky's clock), and every frame after that is a
 * light pass that cross-fades them, forward and back, carries the picture along a
 * slowly turning current and threads fine ridged filaments through the light.
 *
 * Each page lights it in its own hue: <body data-sky="accent|violet|teal|rose|ash|stop">.
 * The appearance is <html data-theme="dark|light"> (else dark).
 * <html class="sky-solid"> turns it off for a plain colour (the app's Background: Solid).
 *
 * Drawn at about half a CSS pixel, a dozen times a second, at the display's rate only
 * while it cross-fades to new colours (3.5 s, SkyState.ease). Still under
 * prefers-reduced-motion, paused while the tab is hidden, never redrawn for a scroll:
 * the picture is 1.35 screens tall and slides at 0.15 of the scroll. sky.css holds the
 * gradient that shows before the first frame, without JS and without WebGL.
 *
 * window.CentrosSky = { setHue(name), setTheme(name), still(bool), settle(bool), reseed(), info() }
 */
(function () {
  'use strict';
  var win = window;
  var doc = document;
  if (win.CentrosSky) return;
  var root = doc.documentElement;

  // ---------------------------------------------------------------------------------
  // Colour. The app resolves iOS system colours, then moves them in HSB the way
  // UIColor.getHue reports them (SkyCanvas.swift: dimmed, lifted, turned).

  var SYSTEM = {
    dark: { blue: [0, 145, 255], cyan: [60, 211, 254], gray: [142, 142, 147], red: [255, 66, 69] },
    light: { blue: [0, 136, 255], cyan: [0, 192, 232], gray: [142, 142, 147], red: [255, 56, 60] }
  };
  var HUES = ['accent', 'violet', 'teal', 'rose', 'ash', 'stop'];

  function toHsb(c) {
    var r = c[0] / 255, g = c[1] / 255, b = c[2] / 255;
    var max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min, h = 0;
    if (d > 0) {
      if (max === r) h = ((g - b) / d) % 6;
      else if (max === g) h = (b - r) / d + 2;
      else h = (r - g) / d + 4;
      h /= 6;
      if (h < 0) h += 1;
    }
    return [h, max > 0 ? d / max : 0, max];
  }
  function toRgb(c) {
    var h = (((c[0] % 1) + 1) % 1) * 6, s = Math.max(0, Math.min(1, c[1])), v = c[2];
    var i = Math.floor(h), f = h - i, p = v * (1 - s), q = v * (1 - s * f), t = v * (1 - s * (1 - f));
    switch (i % 6) {
      case 0: return [v, t, p];
      case 1: return [q, v, p];
      case 2: return [p, v, t];
      case 3: return [p, q, v];
      case 4: return [t, p, v];
      default: return [v, p, q];
    }
  }
  // The same hue at a brightness, fully saturated: the colour deep in shadow.
  function dimmed(c, b) { return [c[0], Math.min(1, c[1] * 1.05), b]; }
  // The same hue lifted towards white: the colour in daylight.
  function lifted(c, b) { return [c[0], c[1] * (1 - b) * 1.6, b]; }
  // A neighbour on the colour wheel.
  function turned(c, t) { return [(c[0] + t + 1) % 1, c[1], c[2]]; }

  // SkyHue.color (Cards.swift).
  function keyOf(hue, dark) {
    var s = dark ? SYSTEM.dark : SYSTEM.light;
    switch (hue) {
      case 'violet': return [0.70, 0.62, 0.92]; // indigo: the night sky, not a purple
      case 'teal': return toHsb(s.cyan);
      case 'rose': return [0.075, 0.85, 0.95]; // amber: sitting at the fire
      case 'ash': return toHsb(s.gray);
      case 'stop': return toHsb(s.red);
      default: return toHsb(s.blue);
    }
  }

  // Home is tempered by the hour (Daylight.byClock, SkyPalette.tempered): a little
  // dimmer at night and brighter by day, never recoloured, from the clock alone.
  function daylightLift() {
    var now = new Date();
    var hour = now.getHours() + now.getMinutes() / 60;
    var x = (hour - 12.75) / 6.25;
    var elevation = 60 * Math.cos(x * Math.PI / 2);
    var day = Math.max(0, Math.min(1, (elevation + 10) / 40));
    return 0.85 + 0.3 * day * day * (3 - 2 * day);
  }

  // SkyPalette.around, and Home's wider arc (SkyArrangement.make, .accent).
  function palette(hue, dark) {
    var k = keyOf(hue, dark);
    var p = {
      own: dark ? dimmed(k, 0.62) : lifted(k, 0.72),
      warm: dark ? dimmed(turned(k, 0.11), 0.52) : lifted(turned(k, 0.09), 0.78),
      cool: dark ? dimmed(turned(k, -0.08), 0.60) : lifted(turned(k, -0.07), 0.70),
      pale: dark ? dimmed(turned(k, -0.03), 0.66) : lifted(k, 0.88),
      deep: dark ? dimmed(k, 0.09) : lifted(k, 0.96),
      far: dark ? dimmed(turned(k, -0.08), 0.60) : lifted(turned(k, -0.07), 0.70),
      edge: dark ? dimmed(turned(k, 0.16), 0.55) : lifted(turned(k, 0.12), 0.82)
    };
    if (hue === 'accent') {
      p.warm = dark ? dimmed(turned(k, 0.14), 0.60) : lifted(turned(k, 0.14), 0.78);
      p.cool = dark ? dimmed(turned(k, -0.13), 0.58) : lifted(turned(k, -0.13), 0.72);
      p.pale = dark ? dimmed(turned(k, 0.30), 0.58) : lifted(turned(k, 0.30), 0.86);
      p.edge = dark ? dimmed(turned(k, 0.22), 0.55) : lifted(turned(k, 0.22), 0.82);
    }
    var out = {};
    for (var name in p) out[name] = toRgb(p[name]);
    if (hue === 'accent' && dark) {
      var lift = daylightLift();
      ['own', 'warm', 'cool', 'pale', 'far', 'edge'].forEach(function (n) {
        out[n] = out[n].map(function (v) { return v * lift; });
      });
    }
    return out;
  }

  // Where each page puts its light: the first three forms of SkyArrangement.make — the
  // masses of the middle plane (x, y in unit screen coordinates, r in screen heights, h
  // how much light gathers, its colour, its own slow clock). The app's two wisps lit a
  // front plane it no longer draws, so they are left out here.
  var FORMS = {
    accent: [[0.78, 0.40, 0.34, 0.16, 'own', 1], [0.16, 0.14, 0.22, 0.22, 'cool', 2], [0.22, 0.88, 0.30, 0.12, 'warm', 3]],
    violet: [[0.15, 0.18, 0.26, 0.18, 'own', 6], [0.50, 0.50, 0.30, 0.14, 'warm', 7], [0.86, 0.82, 0.28, 0.18, 'cool', 8]],
    teal: [[0.30, 0.28, 0.42, 0.14, 'own', 11], [0.74, 0.70, 0.40, 0.14, 'cool', 12], [0.88, 0.22, 0.16, 0.12, 'pale', 13]],
    rose: [[0.50, 1.02, 0.40, 0.24, 'own', 16], [0.18, 1.06, 0.24, 0.14, 'cool', 17], [0.82, 1.06, 0.24, 0.14, 'warm', 18]],
    ash: [[0.50, 0.50, 0.50, 0.06, 'own', 21], [0.20, 0.20, 0.24, 0.05, 'cool', 22], [0.80, 0.80, 0.24, 0.05, 'warm', 23]],
    stop: [[0.50, 0.22, 0.42, 0.24, 'own', 26], [0.12, 0.60, 0.20, 0.08, 'warm', 27], [0.88, 0.62, 0.20, 0.08, 'cool', 28]]
  };
  // What the gas is like: body (0 liquid … 1 billowed), stretch, swirl, pace.
  var CHARACTER = {
    accent: [0, 0.65, 1.1, 1.0], violet: [0, 0.65, 1.1, 1.0],
    teal: [0.1, 0.8, 1.9, 0.8], rose: [0.1, 0.8, 1.9, 0.8],
    ash: [0, 0.7, 0.8, 0.6], stop: [0, 0.7, 0.8, 0.6]
  };
  // Where in the endless noise each page's sky is taken from (SkyArrangement.make): the
  // install's seed, turned a different way for each tab. The site uses the seed of the
  // simulator the design was shot on, so these are the very skies in those screenshots.
  var SEED = 542.278855852546;
  var SEED_KEY = 'centros.sky.seed';   // the account sheet's "New sky" picks another seed, kept in this browser
  (function () {
    var t = null;
    try { t = parseFloat(win.localStorage.getItem(SEED_KEY)); } catch (e) { t = null; }
    if (t && isFinite(t) && t > 0 && t < 1e4) SEED = t;
  })();
  var TURN = { accent: 0, violet: 1, teal: 2, rose: 3, ash: 4, stop: 4 };
  function seedPoint(hue) {
    var a = SEED + TURN[hue] * 2.399, r = 40 + SEED % 17;
    return [Math.cos(a) * r, Math.sin(a) * r];
  }

  function arrangement(hue, dark) {
    var pal = palette(hue, dark);
    return {
      forms: FORMS[hue].map(function (f) {
        return { x: f[0], y: f[1], r: f[2] * 1.4, d: Math.min(1, f[3] * 5.5), c: pal[f[4]], seed: f[5] };
      }),
      deep: pal.deep, far: pal.far, edge: pal.edge,
      shift: seedPoint(hue),
      character: CHARACTER[hue], dark: dark ? 1 : 0
    };
  }

  // SkyState.ease: a smootherstep pulled towards its end, so it eases in for longer
  // than it eases out.
  function ease(x) {
    var p = Math.pow(Math.max(0, Math.min(1, x)), 1.35);
    return p * p * p * (p * (p * 6 - 15) + 10);
  }

  // ---------------------------------------------------------------------------------
  // Shaders. WebGL2 hashes lattice cells with pcg3d on their integer coordinates, as
  // the app does; WebGL1 has no integers to speak of, so it uses a permutation
  // polynomial that stays on exact integers (the README's lesson: never a float hash).

  var VERT1 = 'attribute vec2 aPos;void main(){gl_Position=vec4(aPos,0.0,1.0);}';
  var VERT3 = '#version 300 es\nin vec2 aPos;void main(){gl_Position=vec4(aPos,0.0,1.0);}';

  var HASH3 = [
    'uvec3 pcg3d(uvec3 v){',
    '  v=v*1664525u+1013904223u;',
    '  v.x+=v.y*v.z; v.y+=v.z*v.x; v.z+=v.x*v.y;',
    '  v^=v>>16u;',
    '  v.x+=v.y*v.z; v.y+=v.z*v.x; v.z+=v.x*v.y;',
    '  return v;',
    '}',
    'vec2 hash2(vec2 cell){',
    '  uvec3 h=pcg3d(uvec3(uint(int(cell.x)),uint(int(cell.y)),0x9e37u));',
    '  return vec2(h.xy)*(1.0/4294967295.0);',
    '}'
  ].join('\n');
  var HASH1 = [
    'float permute(float x){return mod((x*34.0+1.0)*x,289.0);}',
    'vec2 hash2(vec2 cell){',
    '  vec2 c=mod(cell,289.0);',
    '  float a=permute(permute(c.x)+c.y);',
    '  float b=permute(a+c.x*7.0+113.0);',
    '  return vec2(a,b)/288.0;',
    '}'
  ].join('\n');

  // Gradient noise, not value noise: lit noise must be.
  var NOISE = [
    'vec2 gradientAt(vec2 cell){return normalize(hash2(cell)*2.0-1.0);}',
    'float noise(vec2 p){',
    '  vec2 i=floor(p); vec2 f=fract(p);',
    '  vec2 u=f*f*f*(f*(f*6.0-15.0)+10.0);',
    '  float a=dot(gradientAt(i),f);',
    '  float b=dot(gradientAt(i+vec2(1.0,0.0)),f-vec2(1.0,0.0));',
    '  float c=dot(gradientAt(i+vec2(0.0,1.0)),f-vec2(0.0,1.0));',
    '  float d=dot(gradientAt(i+vec2(1.0,1.0)),f-vec2(1.0,1.0));',
    '  return mix(mix(a,b,u.x),mix(c,d,u.x),u.y)*0.7+0.5;',
    '}'
  ].join('\n');

  // skyLayer, back plane: the deep sky, the far glow, the gas and the dust.
  var SKY = [
    'uniform vec2 uRes;',     // pixels drawn
    'uniform vec2 uScale;',   // CSS px per pixel
    'uniform vec2 uScreen;',  // the viewport, CSS px
    'uniform float uTime;',
    'uniform float uDrift;',
    'uniform float uDark;',
    'uniform vec3 uDeep;',
    'uniform vec3 uFar;',
    'uniform vec3 uEdge;',
    'uniform vec2 uShift;',
    'uniform vec4 uChar;',
    'uniform vec4 uForm[3];', // x, y, radius, density
    'uniform vec3 uTint[3];',
    'float hash(vec2 p){p=fract(p*vec2(123.34,456.21));p+=dot(p,p+45.32);return fract(p.x*p.y);}',
    'const mat2 TURN=mat2(0.8,0.6,-0.6,0.8);',
    'float fbm(vec2 p,int octaves){',
    '  float value=0.0; float amplitude=0.55;',
    '  for(int i=0;i<5;i++){ if(i>=octaves) break;',
    '    value+=amplitude*noise(p); p=TURN*p*2.0+vec2(17.3,9.1); amplitude*=0.5; }',
    '  return value;',
    '}',
    // Flow noise: each octave drifts its own way, so the sum re-forms as it moves.
    'float flow(vec2 p,float t,int octaves){',
    '  float value=0.0; float amplitude=0.55; vec2 drift=vec2(0.9,0.3);',
    '  for(int i=0;i<5;i++){ if(i>=octaves) break;',
    '    value+=amplitude*noise(p+drift*t); p=TURN*p*2.0+vec2(17.3,9.1);',
    '    drift=TURN*drift*-1.4; amplitude*=0.5; }',
    '  return value;',
    '}',
    'float swell(vec2 d,float radius){return exp(-dot(d,d)/(radius*radius)*1.7);}',
    'const vec2 ALONG=vec2(0.88,0.47);',
    'const vec2 UP=vec2(0.47,-0.88);',
    'struct Glow{float light;float density;float shade;};',
    'Glow glow(vec2 p,float scale,int octaves,bool strands,bool curls,bool volume,float pace,float seed,vec4 ch){',
    '  float s=dot(p,ALONG); float u=dot(p,UP);',
    '  float bubbly=clamp(ch.x,0.0,1.0);',
    '  float airy=max(-ch.x,0.0);',
    '  vec2 q=vec2(s,u*ch.y)*scale*(1.0+0.35*bubbly)+vec2(pace*0.2,seed*5.3);',
    '  vec2 fold=vec2(flow(q*0.5+vec2(3.7,1.9),pace*0.6,2),flow(q*0.5+vec2(-2.3,5.1),pace*0.6,2))-0.5;',
    '  vec2 b=q+fold*ch.z;',
    '  if(curls){',
    '    vec2 swirl=vec2(flow(b*1.1+vec2(-2.3,5.1),pace*0.8,2),flow(b*1.1+vec2(4.4,-1.7),pace*0.8,2))-0.5;',
    '    b+=swirl*vec2(0.45,0.55)*(0.5+0.5*ch.z);',
    '  }',
    '  float n=flow(b,pace,octaves);',
    '  float billow=abs(2.0*n-1.0);',
    '  float ridge=1.0-billow;',
    '  float body=ch.x>=0.0 ? mix(n,n*0.6+sqrt(billow)*0.32+0.06,bubbly) : mix(n,ridge*ridge*0.95,-ch.x);',
    '  float strand=0.0; float grain=1.0;',
    '  if(strands){',
    '    float knot=noise(b*11.0+vec2(pace*1.1,-pace*0.7));',
    '    grain=0.72+0.56*knot;',
    '    float r=1.0-abs(2.0*flow(b*2.2+vec2(7.7,1.3),pace*1.5,2)-1.0);',
    '    float r2=r*r;',
    '    strand=r2*r2*r*smoothstep(0.32,0.62,body);',
    '  }',
    '  Glow g; g.shade=0.7;',
    '  if(volume){',
    '    float toward=flow(b+vec2(-0.10,-0.16),pace,octaves>4?3:2);',
    '    g.shade=smoothstep(-0.10,0.12,n-toward);',
    '  }',
    '  g.density=body+strand*0.25;',
    '  float lo=mix(mix(0.38,0.27,bubbly),0.26,airy);',
    '  float hi=mix(mix(0.64,0.60,bubbly),0.80,airy);',
    '  g.light=smoothstep(lo,hi,body)*0.85*grain+strand*0.5;',
    '  return g;',
    '}',
    'vec3 tinted(vec3 tint,vec3 edge,Glow g){return mix(edge,tint,smoothstep(0.40,0.75,g.density));}',
    'vec3 modelled(vec3 tint,Glow g){return mix(tint*0.55,mix(tint,vec3(1.0),0.12)*1.25,g.shade);}',
    // At night light adds, and hides a third of what is behind it; by day the sky is
    // nearly white and light cannot add to it, so it tints instead.
    'vec3 shoneNight(vec3 rgb,vec3 tint,float light){return rgb*(1.0-min(light,1.0)*0.35)+tint*light;}',
    'vec3 shoneDay(vec3 rgb,vec3 tint,float light){return mix(rgb,tint,light*0.7);}',
    'void main(){',
    '  vec2 position=vec2(gl_FragCoord.x,uRes.y-gl_FragCoord.y);',
    '  vec2 point=position*uScale;',
    '  float aspect=uScreen.x/uScreen.y;',
    '  vec2 uv=point/uScreen;',
    '  vec2 p=vec2(uv.x*aspect,uv.y);',
    '  float t=uTime*0.02;',
    '  float breath=0.95+0.05*sin(uTime*0.09);',
    '  vec2 q=p+uShift;',
    '  vec3 tintSum=vec3(0.0); float weight=0.0;',
    '  for(int i=0;i<3;i++){',
    '    vec4 f=uForm[i];',
    '    float b=swell(p-vec2(f.x*aspect,f.y),f.z)*f.w;',
    '    tintSum+=b*uTint[i]; weight+=b;',
    '  }',
    '  vec3 formTint=tintSum/max(weight,1e-3);',
    '  weight=clamp(weight,0.0,1.0);',
    '  bool night=uDark>0.5;',
    // The deep sky: a little lighter towards the top, the faintest haze at night.
    '  vec3 rgb=night ? uDeep*mix(1.1,0.5,uv.y)*fbm(p*1.6+vec2(t*0.2,0.0),2) : uDeep*mix(1.0,0.98,uv.y);',
    // The far glow, taking a third of the middle plane's share of the look.
    '  vec2 qf=p+uShift/3.0;',
    '  Glow f=glow(qf,3.4,3,false,false,false,uDrift,1.0,uChar);',
    '  vec3 farTint=modelled(tinted(uFar,uEdge,f),f);',
    '  rgb=night ? shoneNight(rgb,farTint,f.light*0.24) : shoneDay(rgb,farTint,f.light*0.24);',
    // The middle plane: the page's own masses of light.
    '  Glow g=glow(q,2.6,5,true,true,true,uDrift,2.0,uChar);',
    '  vec3 gasTint=modelled(tinted(formTint,uEdge,g),g);',
    '  float gasLight=g.light*(0.3+0.7*weight)*0.7;',
    '  rgb=night ? shoneNight(rgb,gasTint,gasLight) : shoneDay(rgb,gasTint,gasLight);',
    // Dimmer at night: a quieter ground lets the cards and the glass lead.
    '  rgb*=breath*(night?0.72:1.0);',
    // Broad lanes of dust far back, and a black point: the darkest goes to true black.
    '  if(night){',
    '    float dust=flow(qf*1.8+vec2(4.1,-2.7),t*0.5,2);',
    '    rgb*=mix(0.3,1.0,smoothstep(0.30,0.52,dust));',
    '    rgb=max(rgb-0.03,0.0)*1.03;',
    '  }',
    // The faintest grain, so the gradients never band: only where there is light.
    '  float lit=min(1.0,max(rgb.r,max(rgb.g,rgb.b))*40.0);',
    '  rgb+=(hash(position+fract(uTime*7.0))-0.5)*(night?0.006:0.004)*lit;',
    '  FRAG=vec4(max(rgb,0.0),1.0);',
    '}'
  ].join('\n');

  // skyFlow: the baked frames made to flow. Two keyframes cross-faded; the picture
  // carried along a broad turning current and a finer one inside it, two staggered
  // copies blended so neither is seen to snap back; and fine ridged filaments, finer
  // than the frames carry, only where there is light. While the page changes colour,
  // the next film fades in over this one. `uBright` settles the sky under a sheet.
  var FLOW = [
    'uniform vec2 uRes;',
    'uniform vec2 uScale;',
    'uniform vec2 uScreen;',
    'uniform float uTime;',
    'uniform float uMix;',
    'uniform float uCross;',
    'uniform float uBright;',
    'uniform sampler2D uA0;',
    'uniform sampler2D uA1;',
    'uniform sampler2D uB0;',
    'uniform sampler2D uB1;',
    'vec3 film(vec2 at){',
    '  vec3 c=mix(TEX(uA0,at).rgb,TEX(uA1,at).rgb,uMix);',
    '  if(uCross>0.0) c=mix(c,mix(TEX(uB0,at).rgb,TEX(uB1,at).rgb,uMix),uCross);',
    '  return c;',
    '}',
    'void main(){',
    '  vec2 position=vec2(gl_FragCoord.x,uRes.y-gl_FragCoord.y);',
    '  vec2 point=position*uScale;',
    '  vec2 size=vec2(uScreen.x,uScreen.y*1.35);',
    '  vec2 uv=point/size.y;',
    '  float slow=uTime*0.03;',
    '  vec2 cur=vec2(noise(uv*1.1+vec2(0.0,slow)),noise(uv*1.1+vec2(5.2,1.3-slow)))-0.5;',
    '  cur+=(vec2(noise(uv*3.1+vec2(slow*1.7,2.0)),noise(uv*3.1+vec2(7.4,-slow*1.7)))-0.5)*0.45;',
    '  cur*=120.0;',
    // Near the edges the current dies away: beyond the frame there is no picture.
    '  vec2 room=min(point,size-point);',
    '  cur*=smoothstep(0.0,90.0,min(room.x,room.y));',
    '  float phase=uTime/6.0;',
    '  float a=fract(phase); float b=fract(phase+0.5);',
    '  float blend=abs(0.5-a)/0.5;',
    '  vec2 p1=point-cur*a; vec2 p2=point-cur*b;',
    '  vec3 c=mix(film(vec2(p1.x/size.x,1.0-p1.y/size.y)),film(vec2(p2.x/size.x,1.0-p2.y/size.y)),blend);',
    '  float fine=mix(noise(p1/size.y*15.0),noise(p2/size.y*15.0+3.7),blend);',
    '  float ridge=1.0-abs(2.0*fine-1.0);',
    '  float lit=clamp(max(c.r,max(c.g,c.b))*6.0,0.0,1.0);',
    '  c*=1.0+(ridge*ridge*0.55-0.18)*lit;',
    '  FRAG=vec4(clamp(c+uBright,0.0,1.0),1.0);',
    '}'
  ].join('\n');

  function fragment(body, gl2) {
    return gl2
      ? '#version 300 es\nprecision highp float;\nprecision highp int;\nout vec4 fragColor;\n#define FRAG fragColor\n#define TEX texture\n' + HASH3 + '\n' + NOISE + '\n' + body
      : 'precision highp float;\n#define FRAG gl_FragColor\n#define TEX texture2D\n' + HASH1 + '\n' + NOISE + '\n' + body;
  }

  // ---------------------------------------------------------------------------------
  // Settings and state.

  var params = (function () {
    try { return new URLSearchParams(win.location.search); } catch (e) { return null; }
  })();
  function param(name) { return params ? params.get(name) : null; }
  function flag(name) { return !!params && params.has(name); }
  // Test switches: ?nosky (the gradient alone), ?skyfreeze=<seconds> (a fixed, still
  // sky, like the app's -centros.freezeSky), ?skyfull (no quality fallback), ?skylive
  // (the shader drawn directly, no film), ?skygl1 (WebGL1), ?skydebug (info().uniforms).
  var FROZEN = param('skyfreeze') !== null && isFinite(parseFloat(param('skyfreeze'))) ? parseFloat(param('skyfreeze')) : null;
  var NO_ADAPT = flag('skyfull');
  var LIVE = flag('skylive');
  var FORCE_GL1 = flag('skygl1');
  var DEBUG = flag('skydebug');
  if (DEBUG && isFinite(parseFloat(param('skyseed')))) {
    // Another install's seed, to compare with its screenshots.
    SEED = parseFloat(param('skyseed'));
  }

  var FRAMES = 6;             // keyframes per film (SkyFilm.frames)
  var HOLD = 6;               // seconds from one keyframe to the next (SkyFilm.hold)
  var MORPH_MS = 3500;        // a change of colour (SkyState.morph)
  var SETTLE_MS = 800;        // a sheet coming up
  var DRIFT_FPS = 12;
  var PARALLAX = 0.15;
  var DEPTH = 0.35;           // the picture is this much taller than the screen
  var BASE_SCALE = 0.5;       // pixels per CSS pixel
  var MAX_PIXELS = 500000;
  var SLOW_MS = 40;
  var SAMPLE_FRAMES = 30;
  var SLOW_BAKE_MS = 400;     // one keyframe bake slower than this (shader compile included): software GL takes seconds
  var STALE_MS = 200;         // a size-only rebake taking longer than this fades to the gradient meanwhile
  var CLOCK_KEY = 'centros.sky.clock';

  var mq = function (q) { return win.matchMedia ? win.matchMedia(q) : null; };
  var reduceMotionQuery = mq('(prefers-reduced-motion: reduce)');
  var darkQuery = mq('(prefers-color-scheme: dark)');
  var forcedQuery = mq('(forced-colors: active)');   // sky.css hides the sky: no context, no loop
  var isForced = function () { return !!(forcedQuery && forcedQuery.matches); };

  var canvas = null, veil = null, gl = null, gl2 = false, quad = null;
  var sky = null, flowProgram = null;           // { program, loc }
  var built = false, drawn = false, lost = false, failed = false;
  var forcedStill = false, slowStill = false;
  var quality = 1, samples = [], samplePrev = 0, samplingDone = false;
  var frameMs = null, bakeMs = [], bakePrev = 0;
  var timer = 0, raf = 0, scrollRaf = 0, resizeTimer = 0;
  var lastTick = 0, lastFrame = 0;
  var cssW = 0, cssH = 0, screenH = 0, extra = 0, lastShift = null;
  var shown = null, incoming = null, baking = null, crossAt = 0; // films
  var settleFrom = 0, settleTo = 0, settleAt = -1e9;
  var probes = 2;             // bakes still to time (the first, and the first after a quality drop)
  var staleSince = 0;

  var clock = loadClock();    // seconds on the sky's clock; it stops while the sky is still
  var hue = readHue(), theme = readTheme();

  function loadClock() {
    var t = null;
    try { t = parseFloat(win.sessionStorage.getItem(CLOCK_KEY)); } catch (e) { t = null; }
    // Carried from page to page within a visit, so the next page's sky carries on.
    return t && isFinite(t) && t > 0 && t < 1e6 ? t : 30;
  }
  function saveClock() {
    try { win.sessionStorage.setItem(CLOCK_KEY, String(clock)); } catch (e) { /* storage blocked */ }
  }

  function readHue() {
    var b = doc.body, v = (b && b.getAttribute('data-sky')) || root.getAttribute('data-sky') || 'accent';
    return HUES.indexOf(v) >= 0 ? v : 'accent';
  }
  function readTheme() {
    var t = root.getAttribute('data-theme');
    if (t === 'dark' || t === 'light') return t;
    return 'dark';
  }
  function isSolid() { return root.classList.contains('sky-solid'); }
  function reduceMotion() { return !!(reduceMotionQuery && reduceMotionQuery.matches); }
  function isStill() { return FROZEN !== null || forcedStill || slowStill || reduceMotion(); }

  function settleAmount(now) {
    var x = (now - settleAt) / SETTLE_MS;
    return x >= 1 ? settleTo : settleFrom + (settleTo - settleFrom) * ease(x);
  }
  function isSettling(now) { return now - settleAt < SETTLE_MS; }

  // Which two keyframes show at a moment and how far the second has faded in: the film
  // plays forward to its last frame and back on one sine, never stopping between frames
  // (SkyReel.position).
  function position(t) {
    var steps = FRAMES - 1, period = 2 * steps * HOLD;
    var x = steps * (0.5 - 0.5 * Math.cos(2 * Math.PI * t / period));
    var from = Math.min(Math.floor(x), FRAMES - 2);
    return { from: from, to: from + 1, mix: x - from };
  }

  // ---------------------------------------------------------------------------------
  // GL.

  function compile(type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS) && !gl.isContextLost()) { gl.deleteShader(s); return null; }
    return s;
  }

  function link(fragmentSource, names) {
    var vs = compile(gl.VERTEX_SHADER, gl2 ? VERT3 : VERT1);
    var fs = compile(gl.FRAGMENT_SHADER, fragmentSource);
    if (!vs || !fs) return null;
    var program = gl.createProgram();
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.bindAttribLocation(program, 0, 'aPos');
    gl.linkProgram(program);
    gl.deleteShader(vs);
    gl.deleteShader(fs);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS) && !gl.isContextLost()) return null;
    var loc = {};
    names.forEach(function (n) { loc[n] = gl.getUniformLocation(program, n); });
    return { program: program, loc: loc };
  }

  // Software GL (a blocklisted or absent GPU) compiles and bakes in seconds on the main thread: such a context is
  // refused and the gradient in sky.css is the sky. Test runs keep it, so screenshots show the shader: any sky test
  // switch, or a browser under automation (headless QA renders through SwiftShader).
  var SOFT_OK = flag('skysoft') || FROZEN !== null || NO_ADAPT || LIVE || FORCE_GL1 || DEBUG || (!flag('skyhard') && !!navigator.webdriver);
  function context(caveat) {
    var attrs = { alpha: false, antialias: false, depth: false, stencil: false, premultipliedAlpha: false,
      preserveDrawingBuffer: DEBUG, powerPreference: 'low-power', failIfMajorPerformanceCaveat: caveat };
    var c = null;
    gl2 = false;
    if (!FORCE_GL1) {
      try { c = canvas.getContext('webgl2', attrs); gl2 = !!c; } catch (e) { c = null; }
    }
    if (!c) {
      try { c = canvas.getContext('webgl', attrs) || canvas.getContext('experimental-webgl', attrs); } catch (e) { c = null; }
    }
    return c;
  }
  function softwareRenderer() {
    var name = '';
    try {
      var ext = gl.getExtension('WEBGL_debug_renderer_info');
      name = String(gl.getParameter(ext ? ext.UNMASKED_RENDERER_WEBGL : gl.RENDERER) || '');
    } catch (e) { name = ''; }
    return /swiftshader|llvmpipe|softpipe|software|basic render/i.test(name);
  }
  function initGL() {
    gl = context(true);
    if (!gl && SOFT_OK) gl = context(false);
    if (!gl) return false;
    if (!SOFT_OK && softwareRenderer()) return false;   // not every browser honours the caveat for every software path
    var hp = gl.getShaderPrecisionFormat && gl.getShaderPrecisionFormat(gl.FRAGMENT_SHADER, gl.HIGH_FLOAT);
    if (!hp || hp.precision < 16) return false; // the noise needs highp
    sky = link(fragment(SKY, gl2), ['uRes', 'uScale', 'uScreen', 'uTime', 'uDrift', 'uDark', 'uDeep', 'uFar', 'uEdge', 'uShift', 'uChar', 'uForm[0]', 'uTint[0]']);
    flowProgram = LIVE ? null : link(fragment(FLOW, gl2), ['uRes', 'uScale', 'uScreen', 'uTime', 'uMix', 'uCross', 'uBright', 'uA0', 'uA1', 'uB0', 'uB1']);
    if (!sky || (!LIVE && !flowProgram)) return false;
    if (flowProgram) {
      gl.useProgram(flowProgram.program);
      gl.uniform1i(flowProgram.loc.uA0, 0);
      gl.uniform1i(flowProgram.loc.uA1, 1);
      gl.uniform1i(flowProgram.loc.uB0, 2);
      gl.uniform1i(flowProgram.loc.uB1, 3);
    }
    quad = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, quad);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    gl.disable(gl.DEPTH_TEST);
    gl.disable(gl.BLEND);
    shown = incoming = baking = null;
    return true;
  }

  // Draws the sky shader (one keyframe, or the live sky) into `fbo` (null: the screen).
  function drawSky(fbo, w, h, arr, time, drift) {
    var loc = sky.loc;
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.viewport(0, 0, w, h);
    gl.useProgram(sky.program);
    gl.uniform2f(loc.uRes, w, h);
    gl.uniform2f(loc.uScale, cssW / w, cssH / h);
    gl.uniform2f(loc.uScreen, cssW, screenH);
    gl.uniform1f(loc.uTime, time);
    gl.uniform1f(loc.uDrift, drift);
    gl.uniform1f(loc.uDark, arr.dark);
    gl.uniform3fv(loc.uDeep, arr.deep);
    gl.uniform3fv(loc.uFar, arr.far);
    gl.uniform3fv(loc.uEdge, arr.edge);
    gl.uniform2fv(loc.uShift, arr.shift);
    gl.uniform4fv(loc.uChar, arr.character);
    var aspect = cssW / screenH, fv = [], tv = [];
    arr.forms.forEach(function (f) {
      // Wandered a little by time, each on its own slow clock; a form pushed off one
      // edge comes back in at the other once wholly off screen (SkyArrangement.packed).
      var x = f.x + Math.sin(time / 53 + f.seed) * 0.022;
      var y = f.y + Math.sin(time / 71 + f.seed * 1.3) * 0.016;
      var my = f.r * 1.6, sy = 1 + 2 * my, mx = my / aspect, sx = 1 + 2 * mx;
      y = ((((y + my) % sy) + sy) % sy) - my;
      x = ((((x + mx) % sx) + sx) % sx) - mx;
      fv.push(x, y, f.r, f.d);
      tv.push(f.c[0], f.c[1], f.c[2]);
    });
    gl.uniform4fv(loc['uForm[0]'], fv);
    gl.uniform3fv(loc['uTint[0]'], tv);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }

  // A film: one page's sky in one appearance at one size, baked to keyframes as needed.
  function Film(hue, theme, w, h) {
    this.hue = hue; this.theme = theme; this.w = w; this.h = h;
    this.seed = SEED;
    this.key = hue + ':' + theme + ':' + w + 'x' + h + ':' + SEED;
    this.arr = arrangement(hue, theme === 'dark');
    this.tex = []; this.fbo = []; this.baked = [];
  }
  Film.prototype.ready = function (pos) { return !!(this.baked[pos.from] && this.baked[pos.to]); };
  Film.prototype.complete = function () { for (var i = 0; i < FRAMES; i++) if (!this.baked[i]) return false; return true; };
  Film.prototype.next = function (pos) {
    if (!this.baked[pos.from]) return pos.from;
    if (!this.baked[pos.to]) return pos.to;
    for (var i = 0; i < FRAMES; i++) if (!this.baked[i]) return i;
    return -1;
  };
  // Keyframe i is the sky at 30 + 6i seconds, as SkyFilm bakes it.
  Film.prototype.bake = function (i) {
    if (!this.tex[i]) {
      var tex = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, this.w, this.h, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
      var fbo = gl.createFramebuffer();
      gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
      if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) throw new Error('sky: framebuffer');
      this.tex[i] = tex; this.fbo[i] = fbo;
    }
    var time = 30 + i * HOLD;
    drawSky(this.fbo[i], this.w, this.h, this.arr, time, 0.02 * time * this.arr.character[3]);
    this.baked[i] = true;
  };
  Film.prototype.free = function () {
    if (gl && !lost) {
      this.tex.forEach(function (t) { if (t) gl.deleteTexture(t); });
      this.fbo.forEach(function (f) { if (f) gl.deleteFramebuffer(f); });
    }
    this.tex = []; this.fbo = []; this.baked = [];
  };

  function bind(unit, tex) { gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, tex); }

  function drawFlow(now, pos) {
    var loc = flowProgram.loc, w = canvas.width, h = canvas.height;
    var cross = incoming ? ease((now - crossAt) / MORPH_MS) : 0;
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, w, h);
    gl.useProgram(flowProgram.program);
    bind(0, shown.tex[pos.from]);
    bind(1, shown.tex[pos.to]);
    bind(2, incoming ? incoming.tex[pos.from] : shown.tex[pos.from]);
    bind(3, incoming ? incoming.tex[pos.to] : shown.tex[pos.to]);
    gl.uniform2f(loc.uRes, w, h);
    gl.uniform2f(loc.uScale, cssW / w, cssH / h);
    gl.uniform2f(loc.uScreen, cssW, screenH);
    gl.uniform1f(loc.uTime, clock % 10000);
    gl.uniform1f(loc.uMix, pos.mix);
    gl.uniform1f(loc.uCross, cross);
    // A sheet over the page: the sky steps back (the app's .brightness(-0.06)).
    gl.uniform1f(loc.uBright, -0.06 * settleAmount(now));
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }

  // The film the page should be showing now; a new one is baked when it changes.
  function wanted() {
    var w = canvas.width, h = canvas.height;
    var latest = baking || incoming || shown;
    var key = hue + ':' + theme + ':' + w + 'x' + h + ':' + SEED;
    if (latest && latest.key === key) return;
    if (baking) { baking.free(); baking = null; }
    if (incoming && shown && shown.key === key) {
      // Turned back mid-change: the film fading out fades back in from where it is.
      var x = Math.min(1, (performance.now() - crossAt) / MORPH_MS), target = 1 - ease(x), lo = 0, hi = 1;
      for (var i = 0; i < 20; i++) { var m = (lo + hi) / 2; if (ease(m) < target) lo = m; else hi = m; }
      var t = shown; shown = incoming; incoming = t;
      crossAt = performance.now() - lo * MORPH_MS;
      return;
    }
    latest = incoming || shown;
    if (latest && latest.key === key) return;
    baking = new Film(hue, theme, w, h);
  }

  // Bakes at most one keyframe: what the screen needs now first, the rest after.
  function bakeOne(pos, still) {
    var films = [baking, shown, incoming], i, f, k;
    for (i = 0; i < films.length; i++) {
      f = films[i];
      if (f && !f.ready(pos)) { f.bake(f.next(pos)); return true; }
    }
    if (still) return false;
    for (i = 0; i < films.length; i++) {
      f = films[i];
      if (f && (k = f.next(pos)) >= 0) { f.bake(k); return true; }
    }
    return false;
  }

  function promote(now, pos, still) {
    if (incoming && now - crossAt >= MORPH_MS) { shown.free(); shown = incoming; incoming = null; }
    if (!baking || !baking.ready(pos) || incoming) return;
    if (!shown) { shown = baking; baking = null; return; }
    // Only the size changed, or nothing moves: no fade.
    var instant = still || (baking.hue === shown.hue && baking.theme === shown.theme && baking.seed === shown.seed);
    if (instant) { shown.free(); shown = baking; }
    else { incoming = baking; crossAt = now; }
    baking = null;
  }

  function hasWork(pos, still) {
    var films = [baking, shown, incoming];
    for (var i = 0; i < films.length; i++) {
      var f = films[i];
      if (f && (!f.ready(pos) || (!still && !f.complete()))) return true;
    }
    return false;
  }

  // Watches the first frames, drawn at the display's rate once the film is baked and
  // the page has loaded: if they come slower than one in 40 ms (the median, so a hitch
  // in the page's own loading is not held against the sky), the resolution halves; if
  // they are still slow, one still frame and no more. Timed by the frames' own cadence:
  // a stall to read the GPU back would cost more than it measures.
  function sampling(still) {
    return !samplingDone && !NO_ADAPT && !still && doc.readyState === 'complete' && !!shown && shown.complete() && !incoming && !baking;
  }
  function adapt(now) {
    if (samplePrev) samples.push(now - samplePrev);
    samplePrev = now;
    if (samples.length < SAMPLE_FRAMES) return;
    var sorted = samples.slice().sort(function (a, b) { return a - b; });
    frameMs = Math.round(sorted[sorted.length >> 1] * 10) / 10;
    samples = [];
    samplePrev = 0;
    if (frameMs <= SLOW_MS) { samplingDone = true; return; }
    if (quality === 1) { quality = 0.5; measure(); return; }
    slowStill = true;
    samplingDone = true;
  }

  // ---------------------------------------------------------------------------------
  // The loop: a dozen frames a second, the display's rate while baking or changing
  // colour, nothing while hidden or still.

  function tick(now) {
    raf = 0;
    if (!built || lost || doc.hidden) return;
    var still = isStill();
    if (!still) clock += lastTick ? Math.min(0.25, Math.max(0, (now - lastTick) / 1000)) : 0;
    lastTick = now;
    var pos = position(clock);
    try {
      if (LIVE) {
        var arr = arrangement(hue, theme === 'dark');
        drawSky(null, canvas.width, canvas.height, arr, clock, 0.02 * clock * arr.character[3]);
        markDrawn();
      } else {
        wanted();
        var t0 = performance.now();
        if (bakeOne(pos, still)) {
          if (probes > 0) probeBake(t0);
          // How long the frames that bake take, for info(): the cadence of those ticks.
          if (bakePrev && bakeMs.length < 12) bakeMs.push(Math.round(now - bakePrev));
          bakePrev = now;
        } else bakePrev = 0;
        promote(now, pos, still);
        var holding = holdWhileResizing(now);
        if (shown && shown.ready(pos) && (!incoming || incoming.ready(pos))) {
          drawFlow(now, pos);
          if (!holding) markDrawn();
          if (sampling(still)) adapt(now); else samplePrev = 0;
        }
      }
    } catch (e) {
      if (gl && gl.isContextLost()) {
        // The context went before its event arrived (a bake then throws): wait for webglcontextrestored.
        lost = true;
        stop();
        shown = incoming = baking = null;
        if (canvas) canvas.classList.remove('is-drawn');
        drawn = false;
        return;
      }
      fail(); // whatever went wrong, the gradient beneath is the sky
      return;
    }
    lastFrame = now;
    schedule(now, pos, still);
  }

  // Times a keyframe bake (one 1-pixel read makes the GPU finish it). Software GL takes seconds per
  // keyframe, so this decides before the other keyframes are baked: half resolution, then one still frame.
  function probeBake(t0) {
    probes--;
    if (NO_ADAPT) { probes = 0; return; }
    var px = new Uint8Array(4);
    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
    var ms = performance.now() - t0;
    if (ms <= SLOW_BAKE_MS) { probes = 0; return; }
    // Seconds per keyframe means software GL: rebaking at half size would block again for as long. Hold still on
    // what is baked (only the two keyframes on screen are ever baked while still).
    if (quality === 1 && ms <= 2 * SLOW_BAKE_MS) { quality = 0.5; measure(); probes = 1; return; }
    slowStill = true;
    samplingDone = true;
    probes = 0;
  }

  // After a resize the film on screen is the old size: CSS would stretch it. If the new film is not ready
  // within STALE_MS, fade to the gradient beneath until it is (a GPU rebakes in a frame or two, unseen).
  function holdWhileResizing(now) {
    var stale = !!shown && (shown.w !== canvas.width || shown.h !== canvas.height);
    if (!stale) { staleSince = 0; return false; }
    if (!staleSince) staleSince = now;
    if (drawn && now - staleSince > STALE_MS) { drawn = false; canvas.classList.remove('is-drawn'); }
    return true;
  }

  function markDrawn() {
    if (drawn) return;
    drawn = true;
    // Shown once the frame is on screen: it fades in over the gradient beneath.
    requestAnimationFrame(function () { if (canvas) canvas.classList.add('is-drawn'); });
  }

  function schedule(now, pos, still) {
    if (!built || lost || doc.hidden || raf || timer) return;
    var busy = !LIVE && (incoming || isSettling(now) || hasWork(pos, still) || sampling(still));
    if (busy) { raf = requestAnimationFrame(tick); return; }
    if (still) { lastTick = 0; return; } // a still sky waits to be asked again
    var wait = Math.max(0, 1000 / DRIFT_FPS - (performance.now() - lastFrame) - 2);
    timer = setTimeout(function () { timer = 0; raf = requestAnimationFrame(tick); }, wait);
  }

  // Draws on the next frame, then carries on if the sky moves.
  function kick() {
    if (!built || lost) return;
    if (timer) { clearTimeout(timer); timer = 0; }
    if (!raf) raf = requestAnimationFrame(tick);
  }

  function stop() {
    if (timer) { clearTimeout(timer); timer = 0; }
    if (raf) { cancelAnimationFrame(raf); raf = 0; }
    lastTick = 0;
  }

  // Sizes the drawing buffer: half a CSS pixel, at most half a million pixels, halved
  // again if the device proved slow. CSS scales it up; the sky is soft.
  function measure() {
    if (!canvas) return;
    var r = canvas.getBoundingClientRect();
    cssW = Math.max(1, r.width);
    cssH = Math.max(1, r.height);
    screenH = cssH / (1 + DEPTH);
    extra = cssH - screenH;
    var k = Math.min(BASE_SCALE, win.devicePixelRatio || 1) * quality;
    var px = cssW * k * cssH * k;
    if (px > MAX_PIXELS) k *= Math.sqrt(MAX_PIXELS / px);
    var w = Math.max(1, Math.round(cssW * k)), h = Math.max(1, Math.round(cssH * k));
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    lastShift = null;
    applyParallax();
  }

  // Parallax: the picture slides at 0.15 of the scroll and is never redrawn for it.
  function applyParallax() {
    scrollRaf = 0;
    if (!canvas) return;
    var y = reduceMotion() ? 0 : Math.min(Math.max(0, (win.pageYOffset || root.scrollTop || 0) * PARALLAX), extra);
    y = Math.round(y * 2) / 2;
    if (y === lastShift) return;
    lastShift = y;
    canvas.style.transform = 'translate3d(0,' + (-y) + 'px,0)';
  }
  function onScroll() { if (!scrollRaf && canvas) scrollRaf = requestAnimationFrame(applyParallax); }

  function onResize() {
    if (resizeTimer) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      resizeTimer = 0;
      if (!built) return;
      measure();
      kick();
    }, 150);
  }

  function onLost(e) {
    e.preventDefault();
    lost = true;
    stop();
    shown = incoming = baking = null; // their textures went with the context
    if (canvas) canvas.classList.remove('is-drawn'); // the gradient beneath shows meanwhile
  }
  function onRestored() {
    lost = false;
    drawn = false;
    var ok = false;
    try { ok = initGL(); } catch (e) { ok = false; }
    if (!ok) { fail(); return; }
    measure();
    kick();
  }

  function retarget() {
    var nextHue = readHue(), nextTheme = readTheme();
    if (nextHue === hue && nextTheme === theme) return;
    hue = nextHue; theme = nextTheme;
    kick();
  }

  // ---------------------------------------------------------------------------------
  // Building and taking down.

  // Phones and tablets keep the CSS gradient sky: baking the shader's keyframes can stall a
  // mobile browser for seconds while the page first paints. ?skyfull still forces it on.
  function isHandheld() {
    var coarse = win.matchMedia && win.matchMedia('(pointer: coarse)').matches;
    return (coarse || Math.min(win.screen.width, win.screen.height) < 768) && !flag('skyfull');
  }

  function build() {
    if (built || failed || isSolid() || isForced() || isHandheld() || flag('nosky') || !doc.body) return;
    canvas = doc.querySelector('canvas.sky');
    if (!canvas) {
      canvas = doc.createElement('canvas');
      canvas.className = 'sky';
      doc.body.insertBefore(canvas, doc.body.firstChild);
    }
    canvas.setAttribute('aria-hidden', 'true');
    veil = doc.querySelector('.sky-veil');
    if (!veil) {
      veil = doc.createElement('div');
      veil.className = 'sky-veil';
      canvas.parentNode.insertBefore(veil, canvas.nextSibling);
    }
    veil.setAttribute('aria-hidden', 'true');
    canvas.addEventListener('webglcontextlost', onLost, false);
    canvas.addEventListener('webglcontextrestored', onRestored, false);
    var ok = false;
    try { ok = initGL(); } catch (e) { ok = false; }
    if (!ok) { fail(); return; }
    built = true;
    drawn = false;
    lost = false;
    root.classList.add('sky-live');
    measure();
    kick();
    announce();
  }

  // Tells the page (portfolio.js: whether "New sky" can do anything) that the sky was built or taken down.
  function announce() {
    try { win.dispatchEvent(new Event('centros:sky')); } catch (e) { /* old browsers: the controls sync on open */ }
  }

  // No WebGL, or it broke: the gradient in sky.css is the sky from here on.
  function fail() {
    failed = true;
    teardown();
  }

  function teardown() {
    stop();
    [shown, incoming, baking].forEach(function (f) { if (f) f.free(); });
    shown = incoming = baking = null;
    if (canvas) {
      canvas.removeEventListener('webglcontextlost', onLost, false);
      canvas.removeEventListener('webglcontextrestored', onRestored, false);
      try {
        var ext = gl && !gl.isContextLost() && gl.getExtension('WEBGL_lose_context');
        if (ext) ext.loseContext(); // hands the GPU memory back now, not at GC
      } catch (e) { /* already gone */ }
      if (canvas.parentNode) canvas.parentNode.removeChild(canvas);
    }
    if (veil && veil.parentNode) veil.parentNode.removeChild(veil);
    canvas = veil = gl = sky = flowProgram = quad = null;
    built = drawn = false;
    if (root.classList.contains('sky-live')) root.classList.remove('sky-live');
    announce();
  }

  function onVisibility() {
    samplePrev = 0;
    if (doc.hidden) { stop(); saveClock(); }
    else { lastTick = 0; kick(); }
  }

  function onMotionChange() {
    lastShift = null;
    applyParallax();
    lastTick = 0;
    kick();
  }

  function listen(query, fn) {
    if (!query) return;
    if (query.addEventListener) query.addEventListener('change', fn);
    else if (query.addListener) query.addListener(fn);
  }

  function start() {
    if (FROZEN !== null) clock = FROZEN;
    hue = readHue();
    theme = readTheme();
    var wasSolid = isSolid();
    new MutationObserver(function () {
      // Only a change of the Background setting builds or takes down the canvas.
      var solid = isSolid();
      if (solid !== wasSolid) {
        wasSolid = solid;
        if (solid) teardown(); else build();
      }
      retarget();
    }).observe(root, { attributes: true, attributeFilter: ['data-theme', 'class', 'data-sky'] });
    if (doc.body) new MutationObserver(retarget).observe(doc.body, { attributes: true, attributeFilter: ['data-sky'] });
    listen(darkQuery, retarget);
    listen(reduceMotionQuery, onMotionChange);
    listen(forcedQuery, function () { if (isForced()) teardown(); else build(); });
    win.addEventListener('scroll', onScroll, { passive: true });
    win.addEventListener('resize', onResize, { passive: true });
    doc.addEventListener('visibilitychange', onVisibility);
    win.addEventListener('pagehide', saveClock);
    win.addEventListener('pageshow', function (e) { if (e.persisted) { lastTick = 0; kick(); } });
    // The sky is the ground, not the content: let the page paint first (sky.css already shows a matching
    // gradient), then compile and bake. Building in the same task as the first frame held text back by
    // up to seconds on slow GPUs; the canvas fades in over the gradient either way.
    var started = false;
    var go = function () { if (!started) { started = true; win.setTimeout(build, 0); } };
    var afterLoad = function (wait) {
      var run = function () { win.requestAnimationFrame(function () { win.requestAnimationFrame(function () { win.setTimeout(go, wait); }); }); };
      if (doc.readyState === 'complete') run(); else win.addEventListener('load', run, { once: true });
    };
    var paintTiming = false;
    try { paintTiming = (win.PerformanceObserver.supportedEntryTypes || []).indexOf('paint') >= 0; } catch (e) { paintTiming = false; }
    if (paintTiming) {
      // Wait for the first contentful paint itself; a hidden tab records none, and the sky does not run there anyway.
      var po = new win.PerformanceObserver(function (list) {
        if (list.getEntriesByName('first-contentful-paint').length) { po.disconnect(); go(); }
      });
      po.observe({ type: 'paint', buffered: true });
      afterLoad(3000);
    } else {
      afterLoad(0);
    }
  }

  win.CentrosSky = {
    // The page's hue: accent, violet, teal, rose, ash or stop. Fades over 3.5 s.
    setHue: function (name) {
      if (HUES.indexOf(name) < 0) return;
      if (doc.body) doc.body.setAttribute('data-sky', name);
      else root.setAttribute('data-sky', name);
      retarget();
    },
    // The appearance: 'dark' or 'light' sets html[data-theme]; anything else clears it
    // and follows prefers-color-scheme.
    setTheme: function (name) {
      if (name === 'dark' || name === 'light') { if (root.getAttribute('data-theme') !== name) root.setAttribute('data-theme', name); }
      else if (root.hasAttribute('data-theme')) root.removeAttribute('data-theme');
      retarget();
    },
    // Holds the sky still (true) or lets it drift again (false).
    still: function (on) {
      forcedStill = !!on;
      lastTick = 0;
      kick();
    },
    // For a sheet over the page: the sky steps back, dimmer, until it goes.
    settle: function (on) {
      var now = performance.now(), target = on ? 1 : 0;
      if (target === settleTo) return;
      settleFrom = settleAmount(now);
      settleTo = target;
      settleAt = isStill() ? -1e9 : now;
      kick();
    },
    // The account sheet's "New sky": another place in the endless noise, faded in over 3.5 s.
    reseed: function () {
      SEED = Math.round((40 + Math.random() * 960) * 1e6) / 1e6;
      try { win.localStorage.setItem(SEED_KEY, String(SEED)); } catch (e) { /* this page view only */ }
      kick();
    },
    info: function () {
      var i = {
        mode: !built ? (isSolid() ? 'solid' : 'fallback') : (gl2 ? 'webgl2' : 'webgl1') + (LIVE ? '-live' : '') + (isStill() ? '-still' : ''),
        hue: hue, theme: theme, seed: SEED, buffer: canvas ? [canvas.width, canvas.height] : null, quality: quality,
        frameMs: frameMs, bakeMs: bakeMs.slice(), drawn: drawn, time: clock, slide: lastShift, reach: extra,
        films: [shown, incoming, baking].map(function (f) { return f ? f.key + ' ' + f.baked.filter(Boolean).length + '/' + FRAMES : null; })
      };
      if (DEBUG && built) {
        var a = arrangement(hue, theme === 'dark');
        i.uniforms = { screen: [cssW, screenH], scale: [cssW / canvas.width, cssH / canvas.height], time: clock, drift: 0.02 * clock * a.character[3],
          dark: a.dark, deep: a.deep, far: a.far, edge: a.edge, shift: a.shift, character: a.character, forms: a.forms };
      }
      return i;
    }
  };

  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', start);
  else start();
})();
