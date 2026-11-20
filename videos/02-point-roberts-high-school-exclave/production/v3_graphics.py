"""Frame-driven cartography for the V3 alternate-road and distance comparison."""
import math
import numpy as np
from scipy.interpolate import PchipInterpolator

from route_v3 import decode,shoreline_measurement
from render_v2 import (KEYS,CROSS,COOL,GOLD,INK,PALE,Route,bus,chip,drawline,event_ring,
                       fade,life,mix,ring,v1)

# Deliberately hold the two-endpoint map long enough to read the road around the bay.
REPLACE={310:(19,17,-123.018,49.007,0),400:(32.5,12,-122.905,48.981,0),
         593:(26,12,-122.996,48.990,-3),928:(23.5,15,-122.950,49.013,0),971:(32.0,14,-122.889,49.020,0),
         1024:(11.1,18,-122.746,49.010,4),1087:(6.7,19,-122.745,48.995,4),
         1323:(9,19,-122.745,49.001,1),1388:(26,13,-122.835,49.025,0),
         1431:(37,12,-122.913,49.015,0),1460:(9.2,22,-123.066,49.001,-5)}
CAM=sorted([(f,*REPLACE[f]) if f in REPLACE else (f,*v) for f,*v in KEYS]+
           [(1404,28,14,-122.852,49.024,0),(1451,22,16,-123.001,49.017,-3)])


class Director:
    keys=CAM
    def __init__(self,land):
        self.out=Route(decode('outbound'),expected=2)
        self.home=Route(decode('homebound'),expected=2)
        a,b=[x[0] for x in self.out.crossings]; c,d=[x[0] for x in self.home.crossings]
        # Bold thick travelled trail, thin future route. The historical segment
        # is a clearly marked cutaway, not a second chronologically moving bus.
        self.otr=PchipInterpolator([42,91,178,206,227,278,350,430,514,583,929,953,995,1012,1021,1041,1073,1095],
            [0,.21*a,.59*a,.85*a,a,a+.016*(b-a),a+.065*(b-a),a+.18*(b-a),a+.25*(b-a),a+.29*(b-a),
             a+.29*(b-a),a+.43*(b-a),a+.81*(b-a),a+.97*(b-a),b,b+.35*(self.out.end-b),b+.84*(self.out.end-b),self.out.end])
        self.rtr=PchipInterpolator([1268,1318,1360,1393,1404,1414,1430,1447,1453,1459,1474,1492],
            [0,.18*c,.55*c,.92*c,c,c+.09*(d-c),c+.42*(d-c),c+.87*(d-c),c+.96*(d-c),d,d+.51*(self.home.end-d),self.home.end])
        self.crossings=[self.out.crossings[0][1],self.out.crossings[1][1],self.home.crossings[0][1],self.home.crossings[1][1]]
        ll,self.dist=shoreline_measurement(land); self.water=v1.grid(ll)
        self.kmi=self.dist*.621371192

    def path(self,f,i,project,wide,route,drive,alpha,color):
        if alpha<.01:return
        # Reveal from the real road's distance, not vertex count or linear latitude.
        d=float(np.clip(drive(i),0,route.end)); trail=project(route.span(0,d))
        allroad=project(route.path)
        drawline(f,allroad,INK,6,.64*alpha); drawline(f,allroad,'#d0b37f' if color==GOLD else '#80b0ad',2,.46*alpha)
        drawline(f,trail,INK,8,.84*alpha); drawline(f,trail,color,10,.15*alpha); drawline(f,trail,color,4,alpha)
        a=project(route.at(d)); look=8 if wide<16 else 45
        forward=project(route.at(min(route.end,d+look)))-project(route.at(max(0,d-look)))
        n=np.linalg.norm(forward)
        if n>1e-3:
            angle=round(-math.degrees(math.atan2(forward[0],-forward[1]))/5)*5
            size=82 if wide<11 else (70 if wide<20 else 58)
            center=a-forward/n*(size*.25)
            v1.paste(f,bus(angle,size),*center,alpha)

    def dashed(self,f,i,project,txt):
        q=life(i,401,590,18); count=fade(i,408,470)
        if q<.01:return
        ends=project(self.water); a,b=ends
        # Navy contrast line stays in the water; dashed teal means comparison,
        # not a road or a claim of present ferry service.
        for start in np.linspace(0,1,27,endpoint=False):
            if start>=count: break
            end=min(count,start+.021); seg=np.stack([a+(b-a)*start,a+(b-a)*end])
            drawline(f,seg,INK,7,q*.90); drawline(f,seg,'#85e2e9',3,q)
        for p in (a,a+(b-a)*count): ring(f,p,5,'#98eef0',q,2)
        pos=(a+b)*.5
        # Distance runs with the advancing measurement head. Descriptor is visible
        # while the line grows and on the deadpan VO beat.
        miles=self.kmi*count; kilometers=self.dist*count
        label=f'{miles:.1f} MI  /  {kilometers:.1f} KM' if count<.995 else f'≈{self.kmi:.0f} MI  /  {self.dist:.0f} KM'
        x=np.clip(pos[0],234,484); y=np.clip(pos[1]+66,570,748)
        s=chip(label,fg='#aaf0f0'); v1.paste(f,s,x,y,q)
        txt('SHORE TO SHORE · NOT A FERRY ROUTE',x,y+32,17,830,PALE,2,q)
        if 533<i<593:
            txt('NO ROAD ACROSS THE BAY',x,y+63,20,850,PALE,2,life(i,533,593,10))
            v1.paste(f,chip('EXAMPLE DRIVE: ≈26 MI / 42 KM',fg=GOLD),374,379,life(i,540,590,10))
        if 533<i<581:
            # The bridge-free comparison points the eye from the water back to the actual road.
            start,end=[v[0] for v in self.out.crossings]
            pr=project(self.out.span(start,mix(start,end,fade(i,533,579))))
            drawline(f,pr,GOLD,3,life(i,533,581,10)*.72)

    def paint(self,f,i,project,wide,marker,txt):
        q=max(life(i,39,590,13),life(i,928,1123,12))
        h=life(i,1267,1510,13)
        self.path(f,i,project,wide,self.out,lambda t:self.otr(np.clip(t,42,1095)),q,GOLD)
        self.path(f,i,project,wide,self.home,lambda t:self.rtr(np.clip(t,1268,1492)),h,COOL)
        self.dashed(f,i,project,txt)
        if q>.05 or h>.05:
            alpha=max(q,h)
            v1.paste(f,chip('EXAMPLE DRIVE · DISTRICT ROUTE UNVERIFIED'),350,1026,alpha)
        # Treat location callouts as traces of evidence, not a stationary dashboard.
        if 174<=i<231:
            marker(project(self.crossings[0]),'BOUNDARY BAY PORT',(-93,-71),life(i,174,231,13),None,COOL)
        if 250<i<328:
            origin=self.out.at(self.out.crossings[0][0]*.35)
            marker(project(origin),'TYEE DRIVE / 56 STREET',(93,59),life(i,250,328,13),None,GOLD)
        if 943<i<1010:
            p=project(self.out.at(self.otr(np.clip(i,42,1095))))
            marker(p,'BRITISH COLUMBIA',(68,64),life(i,943,1010,13),None,COOL)
        if 1002<i<1021:
            marker(project(self.crossings[1]),'PACIFIC HIGHWAY PORT',(76,-72),life(i,1002,1021,6),None,COOL)
        for j,(target,stamp) in enumerate(zip(self.crossings,CROSS)):
            at=project(target); age=i-stamp
            def labels(k):
                return [('BOUNDARY BAY → CANADA',(-63,-67)),('PACIFIC HIGHWAY → U.S.',(-73,-62)),
                        ('PACIFIC HIGHWAY → CANADA',(-61,-71)),('BOUNDARY BAY → WASHINGTON',(-91,-75))][k]
            hold=[54,38,29,49][j]
            if 0<=age<hold:
                label,offset=labels(j)
                event_ring(f,at,True,age,COOL if not j%2 else GOLD)
                marker(at,label,offset,1-fade(age,hold-15,hold),f'{j+1:02}',COOL if not j%2 else GOLD)
        if 1074<i<1126:
            p=project(self.out.path[-1]); q=life(i,1074,1126,8)
            ring(f,p,6,GOLD,q,3)
            event_ring(f,p,False,i-1095,GOLD)
