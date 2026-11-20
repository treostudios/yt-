#!/usr/bin/env python3
"""V2 heightfield documentary renderer; uses the V1 asset/cache acquisition."""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy.interpolate import CubicHermiteSpline, PchipInterpolator
from shapely.geometry import LineString, Point, box, shape
import shapefile

import render as v1

W,H,FPS,N=720,1280,30,1650
AX,AY=354,548
GOLD='#ffca69'; PALE='#fff7e5'; COOL='#ade2de'; INK='#102936'; NIGHT='#0b1c29'
POINT=v1.POINT; SCHOOL=v1.SCHOOL; BLAINE=(-122.7494,48.9958); BAY=(-122.973,48.955); BC=(-122.849,49.077)
# Public mapping transcription derived from International Boundary Commission maps (not a survey).
def dms(d,m,s): return d+m/60+s/3600
BORDER_LL=[(-dms(123,5,26.5),dms(49,0,7.4)),(-dms(123,5,21.7),dms(49,0,7.4)),
           (-dms(123,4,31.1),dms(49,0,7.4)),(-dms(123,4,5.0),dms(49,0,7.4)),
           (-dms(123,3,40.8),dms(49,0,7.5)),(-dms(123,2,10.5),dms(49,0,7.5)),
           (-dms(122,45,26.1),dms(49,0,7.5)),(-122.55,dms(49,0,7.5))]
# Width km, off-nadir pitch degrees, geographic target, heading degrees. The
# camera dolly uses continuous splines; no interpolation is tied to shot chips.
KEYS=[(0,640,8,-123.0676,48.999,0),(11,385,11,-123.0676,48.999,0),
      (33,34,20,-123.0680,48.994,-6),(61,8.6,23,-123.0642,48.993,-8),
      (99,10.1,19,-123.041,48.99,-5),(131,29.5,14,-122.907,48.983,0),
      (165,33,12,-122.903,48.983,0),(184,17.4,17,-123.024,48.994,-4),
      (215,5.6,22,-123.066,48.9998,-7),(255,6.8,21,-123.059,49.001,-5),
      (310,12.8,17,-123.042,48.995,-1),(400,32.5,12,-122.905,48.981,0),
      (468,33.4,12,-122.900,48.984,3),(540,32,12,-122.912,48.981,0),
      (593,23.5,12,-123.004,48.986,-3),(661,13,10,-123.057,48.988,-3),
      (737,10.7,8,-123.061,48.994,0),(882,9.1,8,-123.061,48.991,0),
      (928,10.7,13,-123.054,48.997,-3),(971,32.0,15,-122.899,48.990,0),
      (1024,19.6,18,-122.801,48.988,3),(1087,6.5,22,-122.746,48.992,5),
      (1164,5.6,21,-122.743,48.992,3),(1266,6.4,20,-122.745,48.989,1),
      (1323,17,16,-122.797,48.986,-1),(1388,32.2,12,-122.900,48.983,0),
      (1431,15,18,-123.042,48.995,-3),(1460,6.6,23,-123.066,49.000,-6),
      (1493,9.5,20,-123.058,48.994,-4),(1528,32.4,13,-122.911,48.981,0),
      (1569,33.7,12,-122.902,48.981,0),(1598,39,10,-123.001,48.991,0),
      (1625,150,9,-123.065,48.999,0),(1643,642,8,-123.0676,48.999,0),(1650,640,8,-123.0676,48.999,0)]
CUES=json.loads((v1.ROOT/'production/v2_motion_cues.json').read_text())
CROSS=tuple(m['frame'] for m in CUES['crossings'])


def mix(x,y,q): return x+(y-x)*q

def fade(f,a,b): return v1.smooth((f-a)/(b-a))

def life(f,a,b,r=9): return min(fade(f,a,a+r),1-fade(f,b-r,b))

def bgr(color): return v1.rgb(color)[::-1]


def camera(keys=KEYS):
    a=np.array(keys,dtype=float); t=a[:,0]; y=a[:,1:].copy(); y[:,0]=np.log(y[:,0]); vel=PchipInterpolator(t,y).derivative()(t)
    # Set the same near-seam derivative at the first/last sample.
    vel[[0,-1]]=0
    return CubicHermiteSpline(t,y,vel)


LODX,LODY=1220.,1330.
OV_W,OV_H=1880,2040
OCX,OCY=v1.xy(-123.0676,48.999)
OX=OCX-LODX*v1.KM/2; OY=OCY-LODY*v1.KM/2; OS=OV_W/(LODX*v1.KM)


def overview():
    reader=shapefile.Reader(shp=str(v1.DATA/'ne.shp')); panel=np.zeros((OV_H,OV_W),np.uint8)
    for i,color in ((154,1),(155,2)):
        g=shape(reader.shape(i).__geo_interface__).buffer(0).intersection(box(-135,41,-112,57))
        for p in v1.polys(g):
            cv2.fillPoly(panel,[np.rint((v1.grid(p.exterior.coords)-(OX,OY))*OS).astype(np.int32)],color)
            for r in p.interiors: cv2.fillPoly(panel,[np.rint((v1.grid(r.coords)-(OX,OY))*OS).astype(np.int32)],0)
    land=(panel>0).astype(np.uint8)
    dist=cv2.distanceTransform(1-land,cv2.DIST_L2,5)
    shore=np.exp(-dist/6)
    drop=cv2.GaussianBlur(land.astype(np.float32),(0,0),5)
    drop=np.roll(np.roll(drop,5,0),4,1)
    out=np.empty((*land.shape,3),np.uint8)
    for i,(water,us,ca) in enumerate(zip((49,33,11),(114,148,174),(111,134,87))):
        out[:,:,i]=np.where(panel==1,us,np.where(panel==2,ca,water+shore*14-drop*12)).clip(0,255).astype(np.uint8)
    return out


def heightfield(land,dems):
    dims=(v1.MAP_W,v1.MAP_H); cache=v1.DATA/'v2-height.npy'
    if cache.exists(): return np.load(cache)
    h=np.zeros((dims[1],dims[0]),np.float32)
    for meta, dem in reversed(dems):
        z,w=v1.transform_dem(meta,dem)
        feather=np.minimum(1.,cv2.distanceTransform((w>.6).astype(np.uint8),cv2.DIST_L2,3)/54.)
        h=h*(1-feather)+np.maximum(z,0)*feather
    water=v1.paint_mask(land)==0
    h[water]=0
    # Texture remains unexaggerated; the local surface uses a mild visual scale.
    h=cv2.resize(h*(1.25*v1.KM/1000),(1850,2675),interpolation=cv2.INTER_AREA).astype(np.float32)
    np.save(cache,h)
    return h


def roads(raw, ids, backwards=()):
    parts=[]
    for i in ids:
        coords=raw[i]['coords']
        if i in backwards: coords=coords[::-1]
        ll=[(x,y) for y,x in coords]
        if parts:
            if parts[-1]!=ll[0]: raise ValueError(f'Disconnected road segment {i}')
            parts.extend(ll[1:])
        else: parts.extend(ll)
    return parts


class Route:
    def __init__(self,ll,expected=1):
        self.ll=LineString(ll); path=v1.grid(ll); self.path=path
        self.s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))]; self.end=self.s[-1]
        hit=self.ll.intersection(LineString(BORDER_LL))
        hits=[hit] if hit.geom_type=='Point' else (list(hit.geoms) if hit.geom_type=='MultiPoint' else [])
        if len(hits)!=expected: raise ValueError(f'Expected {expected} road intersections, got {hit.wkt}')
        chain=LineString(path)
        self.crossings=sorted((chain.project(Point(v1.xy(p.x,p.y))),v1.xy(p.x,p.y)) for p in hits)
        self.hit_s,self.hit=self.crossings[0]
    def at(self,d):
        return np.array([np.interp(d,self.s,self.path[:,i]) for i in range(2)])
    def span(self,a,b):
        if b<a: a,b=b,a
        return np.vstack((self.at(a),self.path[(self.s>a)&(self.s<b)],self.at(b)))


def lines(g):
    if g.geom_type=='LineString': return [g] if g.length>.001 else []
    if hasattr(g,'geoms'): return [line for p in g.geoms for line in lines(p)]
    return []


@lru_cache(maxsize=600)
def chip(s,num=None,fg=PALE):
    font=v1.font(20,830); th=font.getlength(s); wid=int(th)+29+(40 if num else 0)
    im=Image.new('RGBA',(wid+8,45)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((5,6,wid+4,43),10,fill=(4,13,19,94))
    d.rounded_rectangle((1,1,wid,38),10,fill=(8,29,41,236),outline=(137,178,180,112))
    left=14
    if num:
        d.rounded_rectangle((5,5,39,34),6,fill=GOLD)
        d.text((22,20),num,font=v1.font(15,850),fill=NIGHT,anchor='mm'); left=46
    d.text((left,20),s,font=font,fill=fg,anchor='lm')
    return v1.form(im)


@lru_cache(maxsize=48)
def bus(angle,size):
    im=Image.new('RGBA',(120,148)); d=ImageDraw.Draw(im)
    # Offset shadow, individual tires, underbody, front/rear glass and destination panel.
    d.rounded_rectangle((28,20,106,138),19,fill=(2,12,17,145))
    for x in (17,87):
        for y in (39,100): d.rounded_rectangle((x,y,x+15,y+19),5,fill='#151e25')
    d.rounded_rectangle((22,16,99,131),16,fill='#a06224',outline='#332c25',width=4)
    d.rounded_rectangle((23,12,95,120),15,fill='#f7b544',outline='#ffe3a0',width=2)
    d.rounded_rectangle((29,19,88,37),6,fill='#213d4b'); d.line((34,20,83,20),fill='#9ddde0',width=2)
    d.rounded_rectangle((31,39,87,100),6,fill='#ffcf68'); d.rounded_rectangle((35,47,83,93),5,outline='#e9a636',width=2)
    for y in range(46,100,10):
        d.line((25,y,30,y),fill='#633c2a',width=2); d.line((89,y,94,y),fill='#8e633a',width=2)
    d.rounded_rectangle((30,105,87,113),3,fill='#683128')
    for x in (33,79):
        d.ellipse((x-3,14,x+3,19),fill='#fffae8'); d.ellipse((x-3,113,x+3,120),fill='#bc4e3b')
    im=im.resize((round(size*.81),size),Image.Resampling.LANCZOS).rotate(angle,Image.Resampling.BICUBIC,expand=True)
    return v1.form(im)


@lru_cache(maxsize=36)
def clock(i):
    im=Image.new('RGBA',(360,130)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((1,2,356,126),17,fill=(9,28,40,243),outline=(161,203,199,127),width=2)
    d.ellipse((20,22,106,108),outline='#385762',width=5)
    if i: d.arc((20,22,106,108),start=-90,end=-90+i*7.6,fill=GOLD,width=5)
    a=i*7.6*math.pi/180; d.line((63,65,63+26*math.sin(a),65-26*math.cos(a)),fill=GOLD,width=3)
    d.ellipse((59,61,67,69),fill=PALE)
    d.text((128,48),'≈40 MIN' if i>=30 else 'TIME ON BUS',font=v1.font(46 if i>=30 else 25,850),anchor='lm',fill=GOLD)
    if i>=31: d.text((130,96),'ONE WAY  →',font=v1.font(20,830),anchor='lm',fill=COOL)
    return v1.form(im)


@lru_cache(maxsize=1)
def slip():
    im=Image.new('RGBA',(515,262)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((17,15,509,260),14,fill=(2,13,20,147)); d.rounded_rectangle((3,3,495,245),12,fill='#f5e5bc',outline='#fff2d7',width=2)
    d.line((30,65,466,65),fill='#a69773',width=2); d.line((30,204,466,204),fill='#a69773',width=1)
    d.text((34,28),'SCHOOL LATE SLIP',font=v1.font(22,850),fill=INK)
    d.text((34,77),'REASON FOR TARDINESS:',font=v1.font(25,800),fill=INK)
    d.text((31,112),'CANADA.',font=v1.font(74,860),fill='#a14633')
    d.text((34,213),'ILLUSTRATION',font=v1.font(13,800),fill='#695d48')
    return v1.form(im.rotate(-3,Image.Resampling.BICUBIC,expand=True))


def drawline(f,p,color,width=2,alpha=1):
    if len(p)<2 or alpha<.01: return
    p=np.rint(p).astype(np.int32); col=bgr(color)
    if alpha>=.995:
        cv2.polylines(f,[p],False,col,width,cv2.LINE_AA); return
    lo=np.maximum(0,np.min(p,axis=0)-width-3); hi=np.minimum((W,H),np.max(p,axis=0)+width+4)
    if np.any(lo>=hi):return
    x,y=lo; xx,yy=hi; r=f[y:yy,x:xx]; k=r.copy()
    cv2.polylines(k,[p-lo],False,col,width,cv2.LINE_AA); cv2.addWeighted(k,alpha,r,1-alpha,0,r)


def water_rim(f,p):
    drawline(f,p,'#70bab6',2,.72)


def ring(f,p,r,color,alpha=1,width=2):
    if alpha<.015:return
    theta=np.linspace(0,2*np.pi,44); drawline(f,np.asarray(p)+np.stack([np.cos(theta)*r,np.sin(theta)*r],1),color,width,alpha)


def event_ring(f,p,k,age,color):
    if not -1<=age<65:return
    for off in (0,9):
        if age<off:continue
        q=min(1,(age-off)/42)
        ring(f,p,12+(48 if k else 34)*q,color,(1-q)**1.4,3 if k else 2)


y_grid,x_grid=np.mgrid[:H,:W].astype(np.float32)
edge=np.clip(1-(.23*((x_grid-350)/407)**2+.13*((y_grid-533)/748)**2),.6,1)
fall=np.clip((y_grid-741)/440,0,.94)
GRADE=np.ascontiguousarray(np.broadcast_to((edge*(1-fall*.87))[:,:,None],(H,W,3)).astype(np.float32))


def render_engine(example_route=False, director_factory=None):
    tex,_,_,_=v1.render_map(); view=overview(); land,us,local,dems=v1.read_assets()
    height=heightfield(land,dems)
    # Territory masks remain geometric and share the camera transform.
    pm=v1.paint_mask(us.intersection(box(-123.106,48.958,-123.017,49.00218)))
    em=v1.paint_mask(us.intersection(box(-122.798,48.969,-122.669,49.00218)))
    mask_bc=v1.paint_mask(land.intersection(box(-123.125,49.00218,-122.64,49.15)))
    ids=np.maximum(np.maximum(pm//255,em//255),mask_bc//255*2).astype(np.uint8)
    # Study coastline and political lines at their own scales.
    bline=land.intersection(LineString(BORDER_LL)); boundary=[v1.grid(x.coords) for x in lines(bline)]
    tip=max(lines(bline.intersection(box(-123.099,48.999,-123.015,49.007))),key=lambda s:s.length)
    if tip.coords[0][0]<tip.coords[-1][0]:tip=LineString(list(tip.coords)[::-1]);
    treaty=Route.__new__(Route); treaty.path=v1.grid(tip.coords); treaty.s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(treaty.path,axis=0),axis=1))]; treaty.end=treaty.s[-1]
    outline=[v1.grid(x.coords) for x in lines(land.boundary.intersection(box(-123.052,48.929,-122.778,49.05))) if x.length>.016]
    out=Route(roads(local['roads'],[241,826,13,478,479,471],(241,826)))
    home=Route(roads(local['roads'],[232,462,452]))
    route_state=None
    custom=director_factory(land,us,treaty) if director_factory else None
    if example_route:
        from v3_graphics import Director
        route_state=Director(land)
    solve=camera(custom.keys if custom else (route_state.keys if route_state else KEYS))
    rq=PchipInterpolator([42,91,180,205,227,248,274],[0,out.hit_s*.17,out.hit_s*.53,out.hit_s*.82,out.hit_s,out.end*.99,out.end])
    hq=PchipInterpolator([1429,1445,1459,1495],[0,home.hit_s*.64,home.hit_s,home.end])
    pos={key:np.array(v1.xy(*ll)) for key,ll in [('point',POINT),('school',SCHOOL),('city',BLAINE),('bay',BAY),('bc',BC),('port',v1.PORT)]}

    def render(fno):
        logwide,pitch,lon,lat,heading=solve(fno); wide=np.exp(logwide)
        k=W/(wide*v1.KM); dy,dx=np.deg2rad([pitch,heading]); cp,sp=np.cos(dy),np.sin(dy); c,s=np.cos(dx),np.sin(dx)
        cx,cy=v1.xy(lon,lat)
        u=(x_grid-AX)/k; v=(y_grid-AY)/(k*cp)
        gx=(cx+c*u-s*v).astype(np.float32); gy=(cy+s*u+c*v).astype(np.float32)
        if wide<90:
            z=cv2.remap(height,gx*.5,gy*.5,cv2.INTER_LINEAR)
            v=v+z*(sp/cp)
            gx=(cx+c*u-s*v).astype(np.float32); gy=(cy+s*u+c*v).astype(np.float32)
        def project(world):
            ar=np.asarray(world); rev=ar.ndim==1; ar=np.atleast_2d(ar).astype(np.float32)
            fx=ar[:,0]; fy=ar[:,1]
            nz=cv2.remap(height,fx.reshape(1,-1)*.5,fy.reshape(1,-1)*.5,cv2.INTER_LINEAR)[0] if wide<90 else np.zeros(len(ar))
            x=fx-cx; y=fy-cy
            ans=np.column_stack((AX+k*(c*x+s*y),AY+k*((-s*x+c*y)*cp-nz*sp)))
            return ans[0] if rev else ans
        detail=1-fade(wide,38,64)
        # Keep extended regional water/land outside the detailed plate when the lens lifts.
        if detail<.999 or wide>24:
            frame=cv2.remap(view,(gx-OX)*OS,(gy-OY)*OS,cv2.INTER_LINEAR,borderValue=(49,33,11))
        else:
            frame=np.full((H,W,3),(55,43,19),np.uint8)
        if detail>.002:
            plate=cv2.remap(tex,gx,gy,cv2.INTER_LINEAR,borderValue=(55,43,19))
            if wide<25:
                np.copyto(frame,plate)
            else:
                room=np.minimum(np.minimum(gx,gy),np.minimum(v1.MAP_W-1-gx,v1.MAP_H-1-gy))
                coeff=(np.clip(room/170,0,1)*detail)[:,:,None]
                frame[:]=frame*(1-coeff)+plate*coeff
        if detail>.22 and not custom:
            same=life(fno,153,195,13)*.31
            tipglow=(life(fno,601,730,18)*.19+life(fno,871,927,14)*.29)
            ca=life(fno,227,275,8)*.29+life(fno,945,1039,19)*.20+life(fno,1404,1469,11)*.24
            usend=life(fno,1459,1506,9)*.29+life(fno,1482,1596,19)*.17
            if same+tipglow+ca+usend>.015:
                m=cv2.remap(ids,gx,gy,cv2.INTER_NEAREST)
                # Shape the highlight out from its evidence; no suggested road on the fallback.
                gain=np.where(m==1,same+tipglow+usend,np.where(m==2,ca,0))
                if 945<fno<1039:
                    frontier=mix(v1.xy(-123.09,49)[0],v1.xy(-122.68,49)[0],fade(fno,945,1015))
                    gain=np.where(m==2,gain*np.clip((frontier-gx+410)/410,0,1),gain)
                for i,val in enumerate((18,46,59)):
                    frame[:,:,i]=np.minimum(255,frame[:,:,i].astype(np.float32)+gain*val).astype(np.uint8)
        cv2.multiply(frame,GRADE,dst=frame,dtype=cv2.CV_8UC3)
        afternoon=0 if custom else life(fno,1267,1618,42)
        if afternoon>.01:
            cv2.addWeighted(frame,1,frame,0,afternoon*2,frame)
        p={a:project(b) for a,b in pos.items()}; exact1=project(out.hit); exact4=project(route_state.crossings[3] if route_state else home.hit)
        def tx(s,x,y,size=26,weight=790,fill=PALE,stroke=1,alpha=1):
            v1.paste(frame,v1.label(s,size,weight,fill,stroke,'',9),x,y,alpha)
        def marker(at, name, off=(0,49), alpha=1, num=None, highlight=GOLD):
            if alpha<.025 or not -45<at[0]<W+42 or not 145<at[1]<960:return
            x,y=at; half=chip(name,num)[1].shape[1]/2 if name else 0
            bx=np.clip(x+off[0],max(64,36+half),min(624,669-half)); by=np.clip(y+off[1],193,811)
            drawline(frame,[(x,y),(x+(bx-x)*.52,y+(by-y)*.62),(bx,by)],highlight,2,alpha*.86)
            ring(frame,at,7,highlight,alpha,3)
            if name: v1.paste(frame,chip(name,num),bx,by,alpha)
        def area(at,name,num,q,sign):
            # Area brackets have no origin dot: these are country transitions, not port pins.
            x=np.clip(at[0],143,558); y=np.clip(at[1]-25,255,775)
            for dr in (-1,1):
                qx=x+dr*110
                drawline(frame,[(qx-dr*15,y-22),(qx,y-22),(qx,y+22),(qx-dr*15,y+22)],sign,2,q*.84)
            v1.paste(frame,chip(name,num),x,y,q)
        if custom:
            for line in boundary:
                a=project(line); drawline(frame,a,INK,5,detail*.85); drawline(frame,a,PALE,2,detail*.75)
            return custom.paint(frame,fno,project,wide,marker,tx,p)
        if detail>.12:
            fade_b=life(fno,30,760,28)+life(fno,864,1614,22)
            for line in boundary:
                a=project(line); drawline(frame,a,INK,5,detail*.84*min(1,fade_b+.15)); drawline(frame,a,PALE,2,detail*.86*min(1,fade_b+.13))
        # Draw the first evidence once as it enters frame, then reveal treaty history separately.
        if 36<=fno<100 and detail>.12:
            seg=treaty.span(0,treaty.end*fade(fno,36,81)); drawline(frame,project(seg),GOLD,3,life(fno,36,100,10))
        if 755<=fno<927:
            progress=fade(fno,758,878); head=treaty.end*progress
            drawline(frame,project(treaty.span(0,head)),GOLD,12,.19*life(fno,755,927,14)); drawline(frame,project(treaty.span(0,head)),GOLD,4,life(fno,755,927,14))
            if .01<progress<.999:
                h=project(treaty.at(head)); ring(frame,h,7+2*math.sin(fno*.37),PALE,1,3)
            a=project(treaty.at(treaty.end*.41)); marker(a,'49° N  ·  HISTORICAL REFERENCE',(35,-46),life(fno,786,921,9))
        # Title structure comes from geographic labels, not interchangeable chapter chips.
        tx('ODD STATE OUT  /  02',347,113,17,840,COOL,1,.95)
        op=life(fno,0,138,12) if 12<fno else 1
        if fno>=1618: op=fade(fno,1618,1650)
        if op>.02:
            tx('THE BORDER BUS',350,254,55,850,PALE,2,op)
        if wide>130:
            k0=fade(wide,130,390)*.86
            q0=project(v1.xy(-123.18,50.48)); q1=project(v1.xy(-121.5,47.44))
            tx('BRITISH COLUMBIA',q0[0]-15,q0[1],18,810,PALE,1,k0)
            tx('WASHINGTON',q1[0]+30,q1[1],18,810,PALE,1,k0)
        if wide>62 or fno<50 or fno>1615:
            anchor=project(out.path[0]); r=12+5*(math.sin(fno*math.tau*16/N)**2)
            ring(frame,anchor,r,GOLD,.94,2); ring(frame,anchor,r+10,GOLD,.28,2)
            if fno<60 or fno>1625:
                q=max(1-fade(fno,38,60),fade(fno,1625,1646))
                v1.paste(frame,bus(0,62),anchor[0],anchor[1]-19,q)
                tx('POINT ROBERTS, WA',anchor[0],anchor[1]+54,20,820,PALE,2,q)
        if not route_state and 39<fno<277:
            d=float(rq(np.clip(fno,42,274))); off=life(fno,37,277,10)
            # Dim remaining road ahead; the amber reveal head is the same world sample as the axle.
            drawline(frame,project(out.path),INK,8,off*.9)
            drawline(frame,project(out.path),'#dcb992',2,off*.66)
            seg=project(out.span(0,d)); drawline(frame,seg,GOLD,10,off*.24); drawline(frame,seg,GOLD,4,off)
            a=project(out.at(d)); v=project(out.at(min(out.end,d+4)))-project(out.at(max(0,d-4)))
            norm=np.linalg.norm(v)
            if norm>.001:
                size=76 if wide<12 else 53; angle=round(-math.degrees(math.atan2(v[0],-v[1]))/5)*5
                center=a-v/norm*(size*.25)
                v1.paste(frame,bus(angle,size),*center,off)
        if not route_state and 1429<=fno<1505:
            d=float(hq(np.clip(fno,1429,1495))); off=life(fno,1429,1505,9)
            drawline(frame,project(home.path),INK,8,off*.85); drawline(frame,project(home.span(0,d)),GOLD,4,off)
            a=project(home.at(d)); v=project(home.at(min(home.end,d+5)))-project(home.at(max(0,d-5)))
            norm=np.linalg.norm(v)
            if norm>.001:
                size=76 if wide<11 else 56; angle=round(-math.degrees(math.atan2(v[0],-v[1]))/5)*5
                v1.paste(frame,bus(angle,size),*(a-v/norm*size*.25),off)
        origin=max(life(fno,65,199,20),life(fno,284,519,17),life(fno,608,923,15),life(fno,1488,1598,13))
        marker(p['point'],'POINT ROBERTS, WA',(-27,49),origin)
        destination=max(life(fno,120,195,12),life(fno,373,600,22),life(fno,1051,1446,13),life(fno,1520,1598,14))
        marker(p['school'] if fno<195 or fno>1048 else p['city'],'BLAINE HIGH SCHOOL' if 1080<fno<1335 else 'BLAINE, WA',
               (-48,-50 if 1080<fno<1335 else 45),destination*(1-life(fno,1196,1278,11)))
        event_ring(frame,p['school'],False,fno-1095,GOLD)
        # Retain readable labels through yaw/zoom; only one water contour at a time.
        q=life(fno,405,593,16)
        if q>.02:
            tx('B O U N D A R Y   B A Y',p['bay'][0],p['bay'][1]+(160 if route_state else 37),19,780,COOL,2,q*(.62 if route_state else 1))
            if 416<=fno<469:
                for line in outline:
                    drawline(frame,project(line),'#83c6c6',2,q*.5*(1-fade(fno,443,469)))
        event_ring(frame,p['city'],False,fno-467,GOLD)
        if not route_state and 184<fno<305:
            marker(exact1,'BOUNDARY BAY PORT' if fno<CROSS[0] else 'ENTER CANADA',(-103,-63),life(fno,184,305,13), '01' if fno>=CROSS[0] else None,COOL)
        if not route_state: event_ring(frame,exact1,True,fno-CROSS[0],COOL)
        if 230<fno<273:
            q=life(fno,230,273,11); v1.paste(frame,v1.flag('CA',248<=fno<252),mix(-70,np.clip(exact1[0]-154,80,575),fade(fno,230,242)),exact1[1]-122,q)
        if not route_state and 247<fno<326:
            marker(project(out.at(out.hit_s*.28)),'TYEE DRIVE / 56 STREET',(100,57),life(fno,247,326,12),None,GOLD)
        if 511<fno<572:
            q=life(fno,511,572,12); v1.paste(frame,v1.flag('US',547<=fno<551),mix(800,np.clip(p['city'][0]-43,170,623),fade(fno,511,525)),p['city'][1]-96,q)
        if 660<fno<769:
            op=life(fno,660,769,14); tx('1846',350,241,85,850,GOLD,2,op); tx('THE OREGON TREATY',350,321,27,850,PALE,2,op)
        if not route_state and 942<fno<1069:
            q=life(fno,942,1069,13); point=p['bc']
            if fno<1021: marker(point,'BRITISH COLUMBIA',(55,-34),q,None,COOL)
            else: area(p['city'],'BACK INTO THE U.S.','02',q,GOLD)
            tx('ROUTE SHOWN SCHEMATICALLY',350,1025,16,820,COOL,2,q)
        if not route_state and 1354<fno<1446:
            q=life(fno,1354,1446,11)
            if 1404<=fno: area(p['bc'],'INTO CANADA','03',q,COOL)
            tx('ROUTE SHOWN SCHEMATICALLY',350,1025,16,820,COOL,2,q)
        if not route_state: event_ring(frame,exact4,True,fno-CROSS[3],GOLD)
        if not route_state and 1459<=fno<1517: marker(exact4,'BACK INTO WASHINGTON',(-77,-54),life(fno,1459,1517,9),'04')
        if route_state: route_state.paint(frame,fno,project,wide,marker,tx)
        if 1110<fno<1220:
            q=life(fno,1110,1220,14); p1=p['school']; cy1=np.clip(p1[1]+170,558,757)
            drawline(frame,[p1,(350,cy1-52)],GOLD,2,q*.7)
            phase=int(30*fade(fno,1116,1154)) if fno<1181 else 31
            v1.paste(frame,clock(phase),350,cy1,q*(1-fade(fno,1206,1220)))
        if 1207<fno<1266:
            q=life(fno,1207,1266,9); cy1=mix(526,696,fade(fno,1207,1220))
            drawline(frame,[p['school'],(348,cy1-111)],GOLD,2,q*.82)
            v1.paste(frame,slip(),349,cy1,q)
        if 1484<=fno<1578:
            q=life(fno,1484,1578,12); k0=fade(fno,1484,1513); x=mix(np.clip(exact4[0],140,590),350,k0); y=mix(np.clip(exact4[1]+58,345,729),762,k0)
            tx('1 + 1 + 1 + 1 = 4',x,y,45,850,GOLD,3,q)
        if 1547<fno<1601:
            tx('ONE SCHOOL DISTRICT',350,332,22,840,PALE,2,life(fno,1547,1601,12))
        if fno<190 or fno>1589:
            tx('© OpenStreetMap contributors  ·  GSHHG  ·  NOAA  ·  GMRT  ·  Natural Earth',351,1100,12,760,COOL,1)
        for c in CUES['source_caption_frames']:
            if c['in_frame']<=fno<c['out_frame']:
                line=c['text']; tone=GOLD if line in ('Canada.','One way.','Four border crossings,') else PALE
                tx(line,347,912,43,830,tone,4);break
        return frame
    return render


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--samples',action='store_true');parser.add_argument('--v3',action='store_true');args=parser.parse_args()
    scene=render_engine(example_route=args.v3)
    if args.samples:
        nums=(0,64,160,239,414,557,679,840,976,1032,1097,1233,1412,1440,1468,1545)
        canvas=Image.new('RGB',(216*4,384*4))
        for i,k in enumerate(nums):
            f=scene(k); cv2.imwrite(str(v1.DATA/f'v2-{k:04}.jpg'),f)
            canvas.paste(Image.fromarray(cv2.resize(f,(216,384))[:,:,::-1]),((i%4)*216,(i//4)*384))
        canvas.save(v1.DATA/('v3-board.jpg' if args.v3 else 'v2-board.jpg'));return
    # Reuse isolated dialogue; the mixed crossings and late-slip paper now conform to V2 marks.
    mix_path=v1.DATA/'v2-mix.wav'
    v1.make_audio(mix_path, crossings=[i/FPS for i in CROSS],
                  whooshes=[(.14,.86),(3.83,1.05),(10.9,.9),(19.55,.74),(30.96,.66),(44.65,.73),(53.50,.68)],
                  line_hit=880/FPS,paper=1207/FPS,bell=1268/FPS)

    tmp=v1.DATA/'video-tmp.mp4'; dest=v1.ROOT/('final_short_v3.mp4' if args.v3 else 'final_short_v2.mp4')
    args=[v1.FFMPEG,'-y','-hide_banner','-loglevel','error','-f','rawvideo','-pixel_format','bgr24','-video_size',f'{W}x{H}',
          '-framerate',str(FPS),'-i','-','-i',str(mix_path),'-filter_threads','1','-vf','scale=1080:1920:flags=lanczos:out_color_matrix=bt709,setsar=1',
          '-af','loudnorm=I=-14:TP=-1.3:LRA=8,aresample=48000','-c:v','libx264','-threads','2','-preset','veryfast','-profile:v','high',
          '-crf','18','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','256k',
          '-bsf:v','h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1',
          '-movflags','+faststart','-metadata','title=The Border Bus (V3)' if args.v3 else 'title=The Border Bus (V2)','-t','55',str(tmp)]
    with subprocess.Popen(args,stdin=subprocess.PIPE) as enc:
        for i in range(N):
            enc.stdin.write(scene(i).tobytes())
            if i%240==0: print(f'{i}/{N} frames',flush=True)
        enc.stdin.close()
        if enc.wait(): raise RuntimeError('FFmpeg encode failed')
    tmp.replace(dest); print(dest,flush=True)


if __name__=='__main__':main()
