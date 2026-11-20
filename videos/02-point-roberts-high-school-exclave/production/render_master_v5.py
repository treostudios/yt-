#!/usr/bin/env python3
"""Render V5 with a perspective street rig, geographic masks and conformed loop pickup."""
import argparse,json,math,subprocess
import cv2,numpy as np
from PIL import Image
from shapely.geometry import Point,box
from render_master_v4 import Director as Base, CAPS, ANCHORS, P, SR, FPS
from render_v2 import (render_engine,chip,bus,drawline,ring,fade,W,H,GOLD,COOL,PALE,INK,v1)
from street_v5 import render as street

A=json.loads((P/'v5_alignment.json').read_text()); N=A['end_frame']; T=N/FPS
WORDS=A['words']; SAMPLES={a:[w for w in WORDS[k] if w[0]==word][n][1] for a,(k,word,n) in ANCHORS.items()}
SAMPLES.update(cross3=SAMPLES['go']+31200,cross4=SAMPLES['customs']+8640,school_close=WORDS['f'][-2][1],bus_close=WORDS['f'][-1][1]); F={k:s//800 for k,s in SAMPLES.items()}
CYAN='#40f4d5'; MINT='#d5fff6'; COBALT='#496bff'; PERI='#b5c5ff'; CRIMSON='#704f60'


def captions():
    spec=dict(CAPS,f=[*CAPS['f'][:-1],(22,25,'on a standard'),(25,28,'yellow school bus.')]); records=[]
    for k,rows in spec.items():
        assert rows[-1][1]==len(WORDS[k])
        for a,b,s in rows:
            records.append((WORDS[k][a][1]//800,math.ceil(WORDS[k][b-1][2]/800),s))
    return [(a,min(b,records[j+1][0]) if j+1<len(records) else b,s) for j,(a,b,s) in enumerate(records)]


def polygons(g):
    if g.geom_type=='Polygon':yield g
    elif hasattr(g,'geoms'):
        for ob in g.geoms:yield from polygons(ob)


class Director(Base):
    frames=F; frame_count=N; custom_bookends=True
    street_renderer=staticmethod(street)
    def caption_rows(self): return captions()
    def __init__(self,land,us,treaty):
        super().__init__(land,us,treaty)
        tip=us.intersection(box(-123.112,48.947,-123.0175,49.0031))
        east=next(g for g in polygons(us) if g.covers(Point(-122.738176,48.992658)))
        bc=land.difference(us)
        self.geo={name:[(v1.grid(p.exterior.coords),[v1.grid(a.coords) for a in p.interiors]) for p in polygons(g.simplify(.00014,preserve_topology=True)) if p.area>1e-6] for name,g in [('tip',tip),('east',east),('bc',bc)]}
        # Start street and match-to-street camera over the same public road.
        self.lift=(122,169); self.map_mix=(145,172)
        self.close_lift=(F['standard']+6,F['school_close']+7)
        self.close_mix=(F['yellow']-3,F['school_close']+7)
        start=(-123.0679,48.9977)
        self.keys=[(0,.14,0,*start,0),(144,.15,1,*start,0),(156,.23,3,*start,0),
            (171,3.15,10,-123.0649,48.9967,0),(F['canada'],8.7,12,-123.060,48.9926,0),
            (F['same']-6,36,10,-122.902,48.987,0),(F['same'],34,10,-122.902,48.987,0),
            (F['point']-5,28,10,-122.944,48.989,0), (F['here']-8,8.9,10,-123.0578,48.9934,0),
            (F['here'],8.7,10,-123.0578,48.9934,0),(F['blaine']-5,8.9,10,-123.0578,48.9934,0),
            (F['blaine']+24,28,11,-122.914,48.989,0),(F['there']-8,6.6,11,-122.7464,48.992,0),
            (F['there'],6.6,11,-122.7464,48.992,0),(F['there']+9,7.3,12,-122.753,48.992,0),
            (F['eleven']-5,33,12,-122.903,48.985,0),(F['across']+23,33,12,-122.903,48.983,0),
            *[k for k in self.keys if F['no']<=k[0]<F['standard']-12],
            (F['standard']-9,12,13,-123.052,48.993,0),(F['standard']+11,6,11,-123.061,48.993,0),
            (F['yellow']+1,1.5,5,-123.067,48.9982,0),(F['school_close']+7,.14,0,*start,0),(N,.14,0,*start,0)]
        assert all(a[0]<b[0] for a,b in zip(self.keys,self.keys[1:]))

    def tint(self,im,proj,key,color,opacity):
        if opacity<=.005:return
        mask=np.zeros((H,W),np.uint8)
        for exterior,interior in self.geo[key]:
            pts=np.rint(np.clip(proj(exterior),-30000,30000)).astype('i');cv2.fillPoly(mask,[pts],255,cv2.LINE_AA)
            for a in interior:
                pts=np.rint(np.clip(proj(a),-30000,30000)).astype('i');cv2.fillPoly(mask,[pts],0,cv2.LINE_AA)
        h=np.array(v1.rgb(color)[::-1],np.float32); a=mask.astype(np.float32)*(opacity/255)
        for j in range(3):im[:,:,j]=np.rint(im[:,:,j]*(1-a)+h[j]*a).astype('uint8')

    def paint(self,im,i,proj,wide,marker,tx,p):
        t=F
        if t['canada']<=i<t['why']:
            self.tint(im,proj,'bc',CRIMSON,.32*(1-fade(i,t['no']+22,t['why'])))
            if i<t['same']:
                marker(proj(self.out.crossings[0][1]),'CANADA',(62,-60),1,None,'#dbb9c2')
        def halo(at,stamp,color,core):
            age=i-stamp
            if 0<=age<63:
                z=math.exp(-age/22);ring(im,at,8,core,z,4);ring(im,at,12+age*.46,color,z,3)
        def campus_pin(at):
            a=np.asarray(at); x,y=np.round(a).astype(int)
            if not 0<x<W or not 0<y<H:return
            q=np.array([(x,y+7),(x-9,y-5),(x,y-14),(x+9,y-5)],np.int32)
            cv2.fillConvexPoly(im,q,v1.rgb(COBALT)[::-1],cv2.LINE_AA)
            cv2.polylines(im,[q],True,v1.rgb(PERI)[::-1],2,cv2.LINE_AA)
        if t['same']<=i<t['point']+5:
            self.tint(im,proj,'tip',CYAN,.29);self.tint(im,proj,'east',COBALT,.38)
            marker(p['point'],'POINT ROBERTS, WA',(92,62),1,None,CYAN)
            marker(p['school'],'BLAINE HIGH, WA',(-88,62),1,None,PERI)
            halo(p['point'],t['same'],CYAN,MINT);halo(p['school'],t['same'],COBALT,PERI)
        if t['here']<=i<t['blaine']+17:
            age=i-t['here'];q=1-fade(i,t['blaine']+2,t['blaine']+17);z=math.exp(-age/23)
            self.tint(im,proj,'tip',CYAN,.36*q)
            a=proj(self.treaty.path);drawline(im,a,CYAN,18,.30*z);drawline(im,a,MINT,4,max(.43,z)*q)
            marker(p['point'],'POINT ROBERTS, WA',(48,66),q,None,CYAN)
            halo(p['point'],t['here'],CYAN,MINT)
            v1.paste(im,chip('48.986° N  ·  123.061° W',fg=MINT),350,753,q)
        if t['there']<=i<t['why']:
            q=1-fade(i,t['no']+23,t['why'])
            self.tint(im,proj,'east',COBALT,.39*q)
            if i>=t['eleven']:
                self.tint(im,proj,'tip',CYAN,.27*q)
                marker(p['point'],'POINT ROBERTS, WA',(80,-62),q,None,CYAN)
            marker(p['school'],'BLAINE HIGH SCHOOL, WA',(-87,-55),q,None,PERI)
            campus_pin(p['school']);halo(p['school'],t['there'],COBALT,PERI)
        if i<t['point'] or i>=t['standard']-9:
            returning=i>=t['standard']-9
            street_i=i-N if returning else i
            # Link both scales to the same road station; street offsets are physically paced.
            station=8+(street_i/60)*10.5*(v1.KM/1000)
            a=proj(self.out.at(max(0,station)))
            m=(1-fade(i,*self.close_mix)) if returning else fade(i,*self.map_mix)
            l=(1-fade(i,*self.close_lift)) if returning else fade(i,*self.lift)
            if m>.005:
                route=proj(self.out.span(0,self.out.crossings[0][0]+210));drawline(im,route,INK,7,.75);drawline(im,route,GOLD,3,.85)
                nearby=proj(self.out.at(max(0,station)+.5))-a
                angle=int(round(-math.degrees(math.atan2(nearby[0],-nearby[1]))/5))*5
                # A registered overview symbol replaces the photometric-sized bus only during the pull-up.
                size=int(48+27*(1-fade(i,171,231))) if not returning else 57
                v1.paste(im,bus(angle,size),*a, max(.14,m))
                if i>=t['canada'] and i<t['point']:tx('WASHINGTON → CANADA → WASHINGTON',350,279,20,840,PALE,2)
            if m<.999:
                ref=np.clip(a,[230,330],[480,710]); scene=self.street_renderer(street_i,align=ref,lift=l)
                if m<=.001:np.copyto(im,scene)
                else:cv2.addWeighted(im,m,scene,1-m,0,im)
        return super().paint(im,i,proj,wide,marker,tx,p)


def output_cues():
    result={'fps':FPS,'sample_rate':SR,'duration_frames':N,'seconds':T,'narrator':'voice-01','cue_source':'V4 stems retained through reverse; new full-sentence closer forced-aligned at 10 ms. Return crossings are timed road actions.', 'cues':[{ 'id':k,'frame':F[k],'audio_marker_sample':SAMPLES[k]} for k in sorted(F,key=F.get)], 'captions':[{'in_frame':i,'out_frame_exclusive':j,'text':s} for i,j,s in captions()]}
    (P/'v5_conformed_cues.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    def stamp(fr):
        n=round(fr*1000/FPS);return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}'
    (P.parent/'final_captions_v5.srt').write_text('\n\n'.join(f'{k}\n{stamp(i)} --> {stamp(j)}\n{s}' for k,(i,j,s) in enumerate(captions(),1))+'\n')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--samples',action='store_true');args=ap.parse_args()
    scene=render_engine(director_factory=Director)
    output_cues()
    if args.samples:
        nums=[0,45,75,101,133,156,171,180,F['same'],F['here']-1,F['here'],F['there']-1,F['there'],F['eleven'],F['no'],F['cross1'],F['four'],F['school_close'],F['bus_close'],N-1]
        board=Image.new('RGB',(216*4,384*5))
        for j,k in enumerate(nums):
            a=scene(k);cv2.imwrite(str(v1.DATA/f'v5-frame-{k}.jpg'),a);board.paste(Image.fromarray(cv2.resize(a,(216,384))[:,:,::-1]),((j%4)*216,(j//4)*384))
        board.save(v1.DATA/'v5-board.jpg');return
    snd=v1.DATA/'v5-mix.wav'; s=lambda k:SAMPLES[k]/SR
    clips=[(P/'voice_v4'/f'{k}.flac',i/SR) for k,i in A['clip_starts'].items() if k!='f']
    clips.extend([(P/'voice_v5/return.flac',A['clip_starts']['f']/SR),(P/'voice_v5/close.flac',A['close_start_sample']/SR)])
    v1.make_audio(snd,dialogue=clips,length=T,loop_street=(2.94,s('standard')),crossings=[s(f'cross{i}') for i in range(1,5)],
        whooshes=[(2.10,.73),(s('loop'),.55),(s('reverse'),.5)],line_hit=s('snip'),paper=s('algebra'),bell=s('after'),
        clicks=[(s('here'),535),(s('there'),650),(s('no'),222),(s('four'),418)])
    dest=P.parent/'final_short_v5.mp4'; tmp=v1.DATA/'v5-video-tmp.mp4'
    cmd=[v1.FFMPEG,'-y','-hide_banner','-loglevel','error','-f','rawvideo','-pixel_format','bgr24','-video_size',f'{W}x{H}',
     '-framerate',str(FPS),'-i','-','-i',str(snd),'-filter_threads','1','-vf','scale=1080:1920:flags=lanczos:out_color_matrix=bt709,setsar=1',
     '-af',f'loudnorm=I=-14:TP=-1.3:LRA=8,aresample=48000,atrim=end_sample={round(T*SR)},asetpts=N/SR/TB','-c:v','libx264','-threads','3','-preset','veryfast','-crf','19','-profile:v','high','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-bsf:v','h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1','-c:a','aac','-b:a','256k','-movflags','+faststart','-t',f'{T:.8f}','-metadata','title=The Border Bus (V5)',str(tmp)]
    with subprocess.Popen(cmd,stdin=subprocess.PIPE) as proc:
        for i in range(N):
            proc.stdin.write(scene(i).tobytes())
            if i%360==0:print(f'{i}/{N}',flush=True)
        proc.stdin.close()
        if proc.wait():raise RuntimeError('FFmpeg failed')
    tmp.replace(dest);print(dest)

if __name__=='__main__':main()
