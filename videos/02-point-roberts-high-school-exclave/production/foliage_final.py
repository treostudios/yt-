"""Layered, world-space evergreen geometry for the final roadside pass."""
import math
from functools import lru_cache
import numpy as np
from street_v5 import box,scenery


def conifer(x,y,height,width,phase,grade,sides):
    def color(c):return ''.join(f'{a:02x}' for a in np.clip(c,0,255).astype(int))
    base=np.array([46,92,76],float)+grade*np.array([8,12,10]); sun=np.array([-.66,-.55,.5]); sun/=np.linalg.norm(sun)
    theta=phase+np.arange(sides)*math.tau/sides
    ground=np.column_stack([x+np.cos(theta)*width*.72+height*.20,y+np.sin(theta)*width*.60+height*.12,np.full(sides,.004)])
    faces=[(ground,'657e6a')]
    r=.09+height*.008
    faces+=box(x-r,x+r,y-r,y+r,0,height*.43,['4e5042','615849','7e6c53','534e40','74634e'])
    for tier,(low,top,scale) in enumerate([(.21,.74,1.0),(.40,.88,.77),(.58,1.0,.54)]):
        a=theta+tier*.085; twist=(np.arange(sides)%2)*.08-.04
        def band(w,z): return np.column_stack((x+np.cos(a)*width*scale*(w+twist),y+np.sin(a)*width*scale*(w+twist),height*(z+twist*.21)))
        rim=band(1,low+.046); inset=band(.70,low)
        point=np.array([x+width*.036*tier,y-width*.033*tier,top*height])
        for k in range(sides):
            j=(k+1)%sides; flank=np.array([rim[k],rim[j],point]); normal=np.cross(flank[1]-flank[0],flank[2]-flank[0]); normal/=np.linalg.norm(normal)
            light=max(0,float(np.dot(normal,sun))); facet=.77+.46*light+.07*tier
            c=base*facet+np.array([18,20,12])*light
            faces.append((np.array([inset[k],inset[j],rim[j],rim[k]]),color(c*.67)))
            faces.append((flank,color(c)))
    return faces


@lru_cache(maxsize=1)
def final_scenery():
    # Keep lane paint and shoulder; replace the single-cone trees only.
    scene=list(scenery()[:3+2+len(range(-110,230,11))])
    rng=np.random.default_rng(112)
    # Camera side is held open so foreground trees do not cover the bus windows.
    for side in (-1,1):
        for j,y0 in enumerate(range(-71,137,7)):
            y=float(y0+rng.uniform(-2.2,2.2)); x=float(side*rng.uniform(6.3,12.9))
            if side>0 and -23<y<41:continue
            h=float(rng.uniform(4.3,8.4)); w=h*float(rng.uniform(.22,.30))
            scene+=conifer(x,y,h,w,float(rng.uniform(0,.9)),float(rng.uniform(-.6,.8)),5)
        for j in range(21):
            y=float(rng.uniform(-92,168)); x=float(side*rng.uniform(17.5,51))
            if side>0 and x<32 and -25<y<45:continue
            h=float(rng.uniform(5.0,10.1)); w=h*float(rng.uniform(.18,.27))
            scene+=conifer(x,y,h,w,float(rng.uniform(0,.9)),float(rng.uniform(-.7,.55)),4)
    return scene
