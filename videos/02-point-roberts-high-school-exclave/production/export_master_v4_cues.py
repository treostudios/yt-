"""Export dialogue cues, actual camera keys, and a frame-addressable animation timeline."""
import csv,json
from pathlib import Path
import numpy as np
from shapely.geometry import box,LineString
from render_master_v4 import ALIGN,F,FPS,LENGTH,N,P,SR,SAMPLES,WORDS,Director,caption_data
from render_v2 import BORDER_LL,Route,camera,lines,v1

land,us,*_=v1.read_assets()
segments=lines(land.intersection(LineString(BORDER_LL)).intersection(box(-123.099,48.999,-123.015,49.007)))
x=max(segments,key=lambda g:g.length); coords=list(x.coords)
if coords[0][0]<coords[-1][0]: coords.reverse()
t=Route.__new__(Route); t.path=v1.grid(coords); t.s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(t.path,axis=0),axis=1))]; t.end=t.s[-1]
d=Director(land,us,t); solve=camera(d.keys)

actions={
'hook_bus':'Yellow bus rolling on Tyee Drive; first frame already reveals the U.S. → Canada → U.S. paradox.',
'canada':'Canada label snaps in and the receiving side of the local border pulses.',
'same':'Both Washington endpoints pulse ochre in the same frame.',
'point':'Pan west to Point Roberts in the same shared terrain rig.',
'here':'Point Roberts land boundary gains an immediate mint core, bloom, locator pulse and coordinate card.',
'blaine':'Transfer the camera through Boundary Bay toward the school.',
'there':'Campus locator pin and expanding ring appear at Blaine High.',
'eleven':'The first red dash and distance tag appear at the measured west endpoint.',
'across':'Red dash head travels east to the measured opposing shore.',
'shortcut':'Complete the red shore-to-shore comparison.',
'no':'Paint the red X, change the descriptor to no bridge, and begin tracing the road around the bay.',
'why':'Clear the bay comparison and begin a continuous move west.',
'piece':'Trace the enclosed southern tip perimeter.',
 'tip_here':'World-space pulse lands on the peninsula in the completed outline.',
'year':'1846 and Oregon Treaty callouts appear.',
'draw':'Neon draw head starts moving west on the land segment.',
'parallel':'49° N historical reference appears without replacing the mapped line.',
'snip':'Line finishes; selected tip reacts, without terrain moving or detaching.',
 'tip':'Second, gentler pulse emphasizes the named peninsula tip.',
'road':'Public Tyee Drive / 56 Street leader; bus approaches the port.',
'foreign':'Canada label appears while the bus briefly holds short of the boundary.',
'cross1':'Bus reaches Boundary Bay intersection, rapid pulse, badge 01, stamp click.',
'loop':'Camera rises and the gold route advances through actual turns around the bay.',
'miles':'Distance card shows the rounded example road distance separately from the red bay span.',
'bc':'British Columbia label; BC-17 and BC-99 pins stay registered to route vertices.',
'cross2':'Bus reaches the Pacific Highway intersection; pulse, badge 02 and click; camera continues to Blaine.',
'arrival':'Approach the campus road on the Blaine mention; settle at public road and reveal campus badge 19 frames later.',
 'two':'Read 2 crossings, one way; no suggestion of two distinct international boundaries.',
'forty':'Reported ≈40 min one-way card appears.',
'prize':'Award card unfolds from the school scene before the pause.',
'algebra':'Instant flip to SOLVE FOR x with one paper click; hold the deadpan.',
'after':'Bell partial; campus departure into homebound sequence.',
'go':'Bus physically advances on the separate homebound geometry.',
'cross3':'Bus reaches the example Pacific Highway return intersection; pulse, badge 03 and click.',
'reverse':'Blue track sweeps around the north shore; soft whoosh.',
'customs':'Return camera tightens onto Boundary Bay; no checkpoint procedures or weapons depicted.',
'cross4':'Bus reaches the Boundary Bay return intersection; pulse, badge 04 and click.',
'four':'Summary settles on 4 BORDER CROSSINGS / PER SCHOOL DAY.',
'day':'School-day denominator remains readable.',
'standard':'Glide to the first shot’s Tyee Drive framing; bus replaces the unfinished spoken noun.',
'yellow':'Hold the matching yellow bus pose through the cut back to “Every morning.”',
}
fx={'here':'click 535 Hz','there':'click 650 Hz','no':'click 222 Hz','snip':'line tick 174 Hz','cross1':'crossing tick 1','cross2':'crossing tick 2','cross3':'crossing tick 3','cross4':'crossing tick 4','loop':'short whoosh','reverse':'short whoosh','algebra':'paper snap','after':'school bell partial','four':'count click 418 Hz'}
assert set(F)==set(actions)
frames=sorted((F[k],k) for k in F)
assert all(0<=i<N and 0<=SAMPLES[k]-i*(SR//FPS)<SR//FPS for i,k in frames)
caps=caption_data();caps=[(a,min(b,caps[i+1][0]) if i+1<len(caps) else b,s) for i,(a,b,s) in enumerate(caps)]
assert all(a<b<=N for a,b,_ in caps)

def ts(a):
    ms=round(a*1000/FPS);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
(P.parent/'final_captions_v4.srt').write_text(''.join(f'{i}\n{ts(a)} --> {ts(b)}\n{s}\n\n' for i,(a,b,s) in enumerate(caps,1)).rstrip()+'\n')
meta={'status':'render timeline from forced alignment','duration_seconds':LENGTH,'fps':FPS,'total_frames':N,'sample_rate':SR,'picture_quantization':'Floor to the containing 60 fps frame from the estimated word onset. Alignment operates on 10 ms acoustic frames; timing is not ground truth to a millisecond.','narrator':'voice-01','dialogue_clip_starts_samples':ALIGN['clip_starts'],
'camera_keys':{'columns':['frame','width_km','off_nadir_pitch_deg','center_lon','center_lat','heading_deg'],'keys':d.keys},
'cues':[{'name':k,'frame':i,'audio_marker_sample':SAMPLES[k],'time_s':round(SAMPLES[k]/SR,5),'source':'timed return action (not a port name)' if k in ('cross3','cross4') else 'forced-aligned word onset','action':actions[k],'sfx':fx.get(k)} for i,k in frames],
'captions':[{'in_frame':a,'out_frame_exclusive':b,'text':s} for a,b,s in caps]}
(P/'v4_master_cues.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n')
with (P/'v4_frame_plan.csv').open('w',newline='') as stream:
    csvw=csv.writer(stream,lineterminator='\n')
    csvw.writerow(['frame','time_s','width_km','pitch','lon','lat','heading','bus_route','chainage_km','cue_starts','caption_id'])
    for i in range(N):
        width,pitch,lon,lat,heading=solve(i); route=''; chain=''
        if i<F['point'] or F['road']<=i<F['after']:
            route='outbound'; chain=f'{float(d.o(np.clip(i,d.o.x[0],d.o.x[-1])))/v1.KM:.6f}'
        elif F['after']<=i<F['four']+52:
            route='homebound'; chain=f'{float(d.h(np.clip(i,d.h.x[0],d.h.x[-1])))/v1.KM:.6f}'
        elif i>=F['standard']-12:
            route='opening_match'; chain=f'{max(1,8-(N-i)*.025)/v1.KM:.6f}'
        csvw.writerow([i,f'{i/FPS:.5f}',f'{np.exp(width):.5f}',f'{pitch:.5f}',f'{lon:.7f}',f'{lat:.7f}',f'{heading:.5f}',route,chain,'|'.join(k for f,k in frames if f==i),next((j for j,(a,b,_) in enumerate(caps,1) if a<=i<b),'')])
print(f'{len(frames)} audio/visual markers · {len(caps)} captions · {N} frame rows')
