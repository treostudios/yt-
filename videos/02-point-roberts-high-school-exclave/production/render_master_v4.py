#!/usr/bin/env python3
"""Render the operator's rewritten master from the conformed dialogue markers."""
from pathlib import Path
import argparse,json,math,subprocess,textwrap
import cv2,numpy as np
from PIL import Image
from scipy.interpolate import PchipInterpolator
from shapely.geometry import box
from render_v2 import (render_engine,Route,chip,bus,drawline,ring,life,fade,lines,
                       W,H,GOLD,COOL,PALE,INK,v1)
from route_v3 import decode,shoreline_measurement

P=Path(__file__).resolve().parent
FPS=60; SR=48000; LENGTH=50.0; N=3000
ALIGN=json.loads((P/'v4_master_alignment.json').read_text()); WORDS=ALIGN['words']

# Every hard hit carries a source dialogue sample; camera paths are permitted to lead.
ANCHORS={
 'hook_bus':('a','bus',0),'canada':('a','canada',0),'same':('a','same',0),
 'point':('b','point',0),'here':('b','here',0),'blaine':('b','blaine',0),'there':('b','there',0),
 'eleven':('b','eleven',0),'across':('b','across',0),'shortcut':('b','shortcut',0),'no':('b','no',0),
 'why':('c','why',0),'piece':('c','piece',0),'tip_here':('c','here',0),'year':('c','eighteen',0),
 'draw':('c','drew',0),'parallel':('c','parallel',0),'snip':('c','snipping',0),'tip':('c','tip',0),
 'road':('c','road',0),'foreign':('c','foreign',0),'cross1':('d','here',0),'loop':('d','loops',0),
 'miles':('d','twenty',0),'bc':('d','british',0),'cross2':('d','u',0),'arrival':('d','blaine',0),
 'two':('d','two',0),'forty':('d','forty',0),'prize':('d','prize',0),'algebra':('e','algebra',0),
 'after':('f','after',0),'go':('f','they',0),'reverse':('f','reverse',0),'customs':('f','customs',0),
 'four':('f','four',0),'day':('f','day',0),'standard':('f','standard',0),'yellow':('f','yellow',0),
}
SAMPLES={a:[w for w in WORDS[k] if w[0]==word][n][1] for a,(k,word,n) in ANCHORS.items()}
# Return crossings are actions inside the reverse leg, not spoken port names.
SAMPLES['cross3']=SAMPLES['go']+int(.65*SR)
SAMPLES['cross4']=SAMPLES['customs']+int(.18*SR)
F={k:s//800 for k,s in SAMPLES.items()}
# Subtitle text is verbatim; ranges refer to each clip's forced-aligned words.
CAPS={
'a':[(0,2,'Every morning,'),(2,6,'this American\nschool bus'),(6,11,'has to drive\nthrough Canada…'),(11,18,'just to stay in\nthe same state.')],
'b':[(0,5,'Point Roberts\nis right here.'),(5,11,'Blaine High is\nright over there.'),(11,17,'It’s eleven miles\nacross the bay.'),(17,19,'Nice shortcut.'),(19,23,'Shame there’s\nno bridge.')],
'c':[(0,4,'So why does\nWashington'),(4,10,'have a piece\nstuck over here?'),(10,15,'In 1846, diplomats'),(15,20,'drew the forty-ninth\nparallel'),(20,24,'straight across\nthe map,'),(24,27,'accidentally\nsnipping off'),(27,31,'this tiny\npeninsula tip.'),(31,37,'Which means the\nonly road out…'),(37,40,'leads straight into'),(40,43,'a foreign country.')],
'd':[(0,5,'So the bus\ncrosses here,'),(5,9,'loops twenty-six\nmiles'),(9,12,'through British\nColumbia,'),(12,16,'and crosses\nback into'),(16,21,'the U.S. at Blaine.'),(21,24,'Two international\nborders.'),(24,26,'Forty minutes.'),(26,32,'And the prize\nat the end?')],
'e':[(0,1,'Algebra.')],
'f':[(0,2,'After school?'),(2,6,'They do the entire'),(6,10,'international commute\nin reverse.'),(10,15,'Which means these\nkids clear'),(15,17,'armed customs'),(17,22,'four times every\nsingle day…'),(22,26,'on a standard\nyellow…')],}

def caption_data():
    result=[]
    for k,rows in CAPS.items():
        w=WORDS[k]
        assert rows[0][0]==0 and rows[-1][1]==len(w),(k,len(w),rows[-1])
        for a,b,s in rows:
            assert 0<=a<b<=len(w)
            result.append((w[a][1]//800,math.ceil(w[b-1][2]/800),s))
    return result

class Director:
    frames=F
    frame_count=N
    custom_bookends=False
    bookend_credits=True
    def caption_rows(self): return caption_data()

    def __init__(self,land,us,treaty):
        F,N=self.frames,self.frame_count
        self.out=Route(decode('outbound'),expected=2); self.home=Route(decode('homebound'),expected=2)
        self.treaty=treaty
        p=us.intersection(box(-123.103,48.95,-123.018,49.00212)); self.tip=[v1.grid(l.coords) for l in lines(p.boundary) if l.length>.025]
        ll,self.km=shoreline_measurement(land);self.water=v1.grid(ll)
        a,b=[s for s,p in self.out.crossings]; c,d=[s for s,p in self.home.crossings]
        self.o=PchipInterpolator([0,F['canada'],F['point'],F['road'],F['foreign']-8,F['cross1']-19,F['cross1'],F['cross1']+25,F['bc'],F['cross2']-16,F['cross2'],F['arrival']+30],
           [8,a*.29,a*.44,a*.62,a-18,a-18,a,a+110,a+(b-a)*.50,b-55,b,self.out.end])
        self.h=PchipInterpolator([F['after']+12,F['cross3'],F['cross3']+14,F['reverse'],F['cross4']-15,F['cross4'],F['four']+17],
           [0,c,c+70,c+.47*(d-c),d-70,d,self.home.end])
        self.hits=[(F['cross1'],self.out.crossings[0][1],'BOUNDARY BAY → CANADA'),(F['cross2'],self.out.crossings[1][1],'PACIFIC HIGHWAY → U.S.'),
                   (F['cross3'],self.home.crossings[0][1],'PACIFIC HIGHWAY → CANADA'),(F['cross4'],self.home.crossings[1][1],'BOUNDARY BAY → U.S.')]
        # Projection never leaves this shared terrain rig. Regional and route bends use the same anchors.
        openview=(9.1,20,-123.061,48.992,-6)
        self.keys=[(0,*openview),(F['canada'],9.4,19,-123.059,48.995,-4),(F['same'],33,12,-122.901,48.987,0),
          (F['point']-5,28,13,-122.931,48.991,0),(F['here'],15,17,-123.032,48.994,-3),
          (F['blaine']+3,34,12,-122.9,48.986,0),(F['there'],16,16,-122.793,48.991,2),
          (F['eleven']-4,29,13,-122.882,48.986,0),(F['across']+23,33,12,-122.903,48.983,0),
          (F['no'],33,12,-122.905,48.983,0),(F['tip_here'],11,14,-123.059,48.994,-2),
          (F['parallel'],10.8,11,-123.061,48.994,0),(F['snip']+35,9,16,-123.060,48.989,-3),
          (F['foreign'],6.3,21,-123.066,49.000,-5),(F['cross1'],6.4,20,-123.066,49.001,-4),
          (F['loop']+16,32,14,-122.943,49.029,0),(F['bc'],38,12,-122.898,49.042,0),
          (F['cross2']-60,29,16,-122.83,49.026,3),(F['cross2'],9,21,-122.740,49.000,3),
          (F['arrival']+29,6.1,22,-122.745,48.991,3),(F['after'],6.1,22,-122.745,48.991,3),
          (F['cross3'],10,20,-122.746,49.010,3),(F['reverse'],36,13,-122.895,49.036,0),
          (F['cross4'],8,20,-123.065,49.002,-4),(F['four']+13,33,12,-122.902,48.987,0),
          (F['standard']-12,14,18,-123.049,48.990,-3),(F['yellow']+11,*openview),(N,*openview)]
        self.keys.sort()
        self.captions=self.caption_rows()
        for (f,w,_),(s,p) in zip(self.hits,[*self.out.crossings,*self.home.crossings]):
            assert abs(float((self.o if f in [F['cross1'],F['cross2']] else self.h)(f))-s)<.0001

    def paint(self,im,i,proj,wide,marker,tx,p):
        t=self.frames; N=self.frame_count
        def hit(k,a=30):
            age=i-t[k];return math.exp(-age/a) if 0<=age<a*4 else 0
        def pop(at,k,color=GOLD):
            z=hit(k,19)
            if z:
                ring(im,at,8,color,z,4);ring(im,at,10+(i-t[k])*.44,color,z*.8,2)
        def card(s,x=350,y=741,fg=PALE): v1.paste(im,chip(s,fg=fg),x,y,1)
        def road(r,chain,visited,color):
            drawline(im,proj(r.path),INK,7,.82);drawline(im,proj(r.path),'#ddcdb3',2,.76)
            if visited: drawline(im,proj(r.span(0,chain)),color,4,1)
        def vehicle(r,d,size):
            a=proj(r.at(d)); dr=proj(r.at(min(d+11,r.end)))-proj(r.at(max(d-11,0)))
            ang=round(-math.degrees(math.atan2(dr[0],-dr[1]))/5)*5
            v1.paste(im,bus(ang,size),*a,1)
        drive1=t['road']<=i<t['after']; drive2=t['after']<=i<t['four']+52
        opening=i<t['point'] or i>=t['standard']-12
        wrap=i>=t['standard']-12
        show_route=t['no']<=i<t['why'] or drive1 or drive2
        if show_route:
            rr=self.home if drive2 else self.out
            curve=self.h if drive2 else self.o
            d=float(curve(np.clip(i,*[curve.x[j] for j in (0,-1)])))
            road(rr,d,drive1 or drive2,COOL if drive2 else GOLD)
            if not (drive1 or drive2):
                progress=.012+.988*fade(i,t['no'],t['why']-9)
                drawline(im,proj(rr.span(0,rr.end*progress)),GOLD,3,.85)
        if not self.custom_bookends and t['here']<=i<t['here']+65:
            a=proj(self.treaty.path); age=i-t['here']; z=math.exp(-age/46)
            drawline(im,a,'#75f6e8',17,.37*z); drawline(im,a,'#edfdf8',4,z)
            pop(p['point'],'here',COOL)
            marker(p['point'],'POINT ROBERTS, WA',(45,72),z,None,COOL)
            card('48.986° N  ·  123.061° W',350,757,COOL)
        if not self.custom_bookends and t['same']<=i<t['point']+6:
            marker(p['point'],'POINT ROBERTS, WA',(32,55),1,None,GOLD)
            marker(p['school'],'BLAINE HIGH SCHOOL',(-72,52),1,None,GOLD)
            pop(p['point'],'same');pop(p['school'],'same')
        if not self.custom_bookends and t['there']<=i<t['why']:
            marker(p['school'],'BLAINE HIGH SCHOOL',(-75,-69),1,None,GOLD)
            pop(p['school'],'there')
        if t['eleven']<=i<t['why']+5:
            a,b=proj(self.water); g=.025 if i<t['across'] else .025+.975*fade(i,t['across'],t['shortcut']-7)
            color='#ff786b'
            for j in range(25):
                start=j/25;end=min(start+.024,g)
                if end<=start:break
                stroke=np.stack([a+(b-a)*start,a+(b-a)*end]);drawline(im,stroke,INK,7,.88);drawline(im,stroke,color,4,1)
            ring(im,a,5,color,1,2);ring(im,a+(b-a)*g,5,color,1,2)
            if i>=t['no']:
                m=(a+b)*.5
                for s in [-1,1]: drawline(im,[m+[-15,s*-15],m+[15,s*15]],'#ff897a',6,1)
            card('≈11 MI / 18 KM',350,638,'#ffb29d');tx('NO BRIDGE · NOT A FERRY ROUTE' if i>=t['no'] else 'BOUNDARY BAY · SHORE TO SHORE',350,683,19,850,PALE,3)
        if t['piece']<=i<t['road']:
            q=fade(i,t['piece']-1,t['tip_here']); q=max(q,.15)
            for a in self.tip:
                end=max(2,math.ceil(len(a)*q))
                drawline(im,proj(a[:end]),GOLD,3,.83)
            pop(p['point'],'tip_here');pop(p['point'],'tip')
        if t['year']<=i<t['road']:
            tx('1846',350,297,59,860,GOLD,3)
            tx('OREGON TREATY',350,356,24,820,PALE,2)
            if i>=t['draw']:
                q=.025+.975*fade(i,t['draw'],t['snip']); d=self.treaty.end*q
                a=proj(self.treaty.span(0,d))
                drawline(im,a,'#8affeb',14,.30);drawline(im,a,'#e0fff5',4,1);ring(im,proj(self.treaty.at(d)),6,COOL,1,3)
            if i>=t['parallel']:card('49° N  ·  HISTORICAL REFERENCE',350,748,COOL)
            if i>=t['snip']:pop(p['point'],'snip')
        if drive1 or drive2:
            vehicle(rr,d,81 if wide<14 else 59)
            card('EXAMPLE DRIVE · DISTRICT ROUTE UNVERIFIED',349,1011,COOL)
        if t['road']<=i<t['cross1']:
            marker(proj(self.out.crossings[0][1]),'TYEE DRIVE / 56 STREET',(-66,-64),1,None,GOLD)
            if i>=t['foreign']: tx('CANADA',349,315,30,850,COOL,3)
        if t['miles']<=i<t['cross2']-24:
            card('≈26 MI  ·  BC-17 → BC-99',350,649,GOLD)
            if i>=t['bc']:tx('BRITISH COLUMBIA',350,286,30,850,COOL,3)
            # Road tags are tied to sample vertices on each numbered highway.
            marker(proj(self.out.path[221]),'BC-17',(-29,-51),1,None,GOLD)
            marker(proj(self.out.path[386]),'BC-99',(37,-50),1,None,GOLD)
        for j,(f,w,name) in enumerate(self.hits,1):
            z=i-f; stop=35 if j==4 else 68
            if 0<=z<stop:
                a=proj(w);q=1-fade(z,stop-16,stop);c=COOL if j%2 else GOLD
                ring(im,a,10+z*.50,c,q,3);ring(im,a,7,c,q,4)
                marker(a,name,(-65,-77),q,str(j).zfill(2),c)
        if t['arrival']+19<=i<t['after']:
            marker(p['school'],'BLAINE HIGH SCHOOL',(-52,-63),1,None,GOLD)
        if t['two']<=i<t['prize']:
            card('2 CROSSINGS  ·  ONE WAY',350,617,COOL)
        if t['forty']<=i<t['prize']:
            tx('≈40 MIN',350,674,51,850,GOLD,3);tx('REPORTED ONE WAY',350,723,17,830,PALE,2)
        if t['prize']<=i<t['after']:
            y=692; x=350; mathbeat=i>=t['algebra']; fg='#fff4d6' if mathbeat else '#ffd47d'
            q=max(.24,fade(i,t['prize'],t['prize']+15)); ht=round(103*q)
            cv2.rectangle(im,(x-154,y-ht//2),(x+158,y+ht//2+7),(24,34,37),-1)
            cv2.rectangle(im,(x-156,y-ht//2),(x+155,y+ht//2),v1.rgb(fg)[::-1],-1)
            if q>.5:
                tx('FIRST PERIOD' if mathbeat else 'AND THE PRIZE IS…',x,y-18,17,850,INK,0)
                if mathbeat:
                    tx('SOLVE FOR x',x,y+16,36,850,INK,0)
                else:
                    theta=np.arange(10)*math.pi/5-math.pi/2
                    r=np.where(np.arange(10)%2,7,16)
                    star=np.round(np.stack((x+r*np.cos(theta),y+17+r*np.sin(theta)),axis=1)).astype(np.int32)
                    cv2.fillPoly(im,[star],v1.rgb(INK)[::-1],lineType=cv2.LINE_AA)
        if t['four']<=i<t['standard']-12:
            tx('4 BORDER CROSSINGS',350,695,36,880,GOLD,3);tx('PER SCHOOL DAY',350,739,19,840,PALE,2)
        if opening and not self.custom_bookends:
            if wide<15:
                drawline(im,proj(self.out.span(0,self.out.crossings[0][0]+210)),INK,5,.74)
                drawline(im,proj(self.out.span(0,self.out.crossings[0][0]+210)),GOLD,2,.83)
            dd=float(self.o(min(i,t['point']))) if not wrap else max(1,8-(N-i)*.025)
            vehicle(self.out,dd,98 if wide<15 else 59)
            if i<t['canada'] or wrap:
                tx('THE BORDER BUS',350,311,46,870,PALE,3)
                tx('WASHINGTON → CANADA → WASHINGTON',350,361,20,840,COOL,2)
            elif i<t['same']:tx('CANADA',350,318,37,850,COOL,3);pop(proj(self.out.crossings[0][1]),'canada',COOL)
        if not self.custom_bookends or not opening: tx('ODD STATE OUT  /  02',350,139,16,840,COOL,1)
        if opening and self.bookend_credits:tx('© OpenStreetMap contributors · GSHHG · NOAA · GMRT',349,1090,13,770,COOL,1)
        for a,b,s in reversed(self.captions):
            if a<=i<b:
                settings=s.splitlines(); yy=889 if len(settings)==2 else 921
                for m,line in enumerate(settings):tx(line,350,yy+m*48,43,850,GOLD if s=='Algebra.' else PALE,4)
                break
        return im


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--samples',action='store_true');args=ap.parse_args()
    scene=render_engine(director_factory=Director)
    if args.samples:
        nums=[0,F['canada'],F['here'],F['there'],F['across']+30,F['no'],F['parallel'],F['snip'],F['cross1'],F['bc'],F['cross2'],F['forty'],F['algebra'],F['cross3'],F['cross4'],F['four'],N-1]
        board=Image.new('RGB',(216*4,384*5))
        for j,k in enumerate(nums):
            a=scene(k);cv2.imwrite(str(v1.DATA/f'v4-frame-{k}.jpg'),a);board.paste(Image.fromarray(cv2.resize(a,(216,384))[:,:,::-1]),((j%4)*216,(j//4)*384))
        board.save(v1.DATA/'v4-board.jpg');return
    snd=v1.DATA/'v4-mix.wav'; s=lambda k:SAMPLES[k]/SR
    v1.make_audio(snd,dialogue=[(P/'voice_v4'/f'{k}.flac',i/SR) for k,i in ALIGN['clip_starts'].items()],length=LENGTH,
        crossings=[s(f'cross{i}') for i in range(1,5)],whooshes=[(s('loop'),.55),(s('reverse'),.5)],line_hit=s('snip'),paper=s('algebra'),bell=s('after'),
        clicks=[(s('here'),535),(s('there'),650),(s('no'),222),(s('four'),418)])
    dest=v1.ROOT/'final_short_v4.mp4'; tmp=v1.DATA/'v4-video-tmp.mp4'
    cmd=[v1.FFMPEG,'-y','-hide_banner','-loglevel','error','-f','rawvideo','-pixel_format','bgr24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','-', '-i',str(snd),'-filter_threads','1','-vf','scale=1080:1920:flags=lanczos:out_color_matrix=bt709,setsar=1','-af','loudnorm=I=-14:TP=-1.3:LRA=8,aresample=48000','-c:v','libx264','-threads','3','-preset','veryfast','-crf','19','-profile:v','high','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-bsf:v','h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1','-c:a','aac','-b:a','256k','-movflags','+faststart','-metadata','title=The Border Bus (V4)',str(tmp)]
    with subprocess.Popen(cmd,stdin=subprocess.PIPE) as proc:
        for i in range(N):
            proc.stdin.write(scene(i).tobytes())
            if i%360==0:print(f'{i}/{N}',flush=True)
        proc.stdin.close()
        if proc.wait():raise RuntimeError('FFmpeg failed')
    tmp.replace(dest);print(dest)

if __name__=='__main__':main()
