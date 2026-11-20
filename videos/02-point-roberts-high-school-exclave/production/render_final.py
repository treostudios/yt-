"""Apply the final finishing pass to V5, without changing editorial timing."""
import argparse,subprocess
import cv2
from PIL import Image
from foliage_final import final_scenery
from render_master_v5 import Director, P, F, N, T, SR, SAMPLES, A, v1, render_engine
from street_v5 import render as street

class FinalDirector(Director):
    bookend_credits=False
    @staticmethod
    def street_renderer(frame, **kwargs):
        return street(frame,scenery_factory=final_scenery,**kwargs)

START_CREDIT,END_CREDIT=1700,1940
OSM='Map data © OpenStreetMap contributors · ODbL'
CREDITS=OSM+' (https://www.openstreetmap.org/copyright); shoreline: GSHHG; basemap: Natural Earth; terrain: NOAA CUDEM and GMRT Synthesis (https://www.gmrt.org/about/terms_of_use.php).'
FF=v1.FFMPEG
ALPHA='loudnorm=I=-14:TP=-1.3:LRA=8,aresample=48000,atrim=end_sample='+str(round(T*SR))+',asetpts=N/SR/TB'
ENCODE=['-c:v','libx264','-threads','4','-preset','veryfast','-crf','18','-profile:v','high','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-bsf:v','h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1']
COMMON=['-t',f'{T:.8f}','-movflags','+faststart','-metadata','title=The Border Bus','-metadata','comment='+CREDITS]


def audio(target):
    s=lambda k:SAMPLES[k]/SR
    clips=[(P/'voice_final/algebra.flac' if k=='e' else P/'voice_v4'/f'{k}.flac',i/SR) for k,i in A['clip_starts'].items() if k!='f']
    clips.extend([(P/'voice_v5/return.flac',A['clip_starts']['f']/SR),(P/'voice_v5/close.flac',A['close_start_sample']/SR)])
    v1.make_audio(target,dialogue=clips,length=T,clip_gains={P/'voice_final/algebra.flac':16.0},loop_street=(2.94,s('standard')),crossings=[s(f'cross{i}') for i in range(1,5)],
        whooshes=[(2.10,.73),(s('loop'),.55),(s('reverse'),.5)],line_hit=s('snip'),paper=s('algebra'),bell=s('after'),
        clicks=[(s('here'),535),(s('there'),650),(s('no'),222),(s('four'),418)])


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--samples',action='store_true');args=cli.parse_args()
    scene=render_engine(director_factory=FinalDirector)
    if args.samples:
        idx=[0,34,75,91,105,132,148,171,2990,3020]; board=Image.new('RGB',(216*5,384*2))
        for j,i in enumerate(idx):
            img=scene(i);cv2.imwrite(str(v1.DATA/f'final-frame-{i}.jpg'),img)
            board.paste(Image.fromarray(cv2.resize(img,(216,384))[:,:,::-1]),(216*(j%5),384*(j//5)))
        board.save(v1.DATA/'final-board.jpg');return
    dest=P.parent/'final_short_master.mp4'; pub=P.parent/'final_short_publish.mp4'
    snd=v1.DATA/'master-mix.wav'; audio(snd)
    original=P.parent/'final_short_v5.mp4';size=1080*1920*3
    dec=[FF,'-v','error','-threads','3','-i',str(original),'-an','-pix_fmt','bgr24','-f','rawvideo','-threads','1','pipe:1']
    args=[FF,'-y','-v','error','-f','rawvideo','-video_size','1080x1920','-pixel_format','bgr24','-framerate','60','-i','-','-i',str(snd),'-filter_threads','1',
         '-vf','scale=out_color_matrix=bt709,setsar=1','-af',ALPHA,*ENCODE,'-c:a','aac','-b:a','256k',*COMMON,str(dest)]
    with subprocess.Popen(dec,stdout=subprocess.PIPE) as d, subprocess.Popen(args,stdin=subprocess.PIPE) as e:
        for i in range(N):
            old=d.stdout.read(size)
            if len(old)!=size:raise RuntimeError(f'V5 decode stopped at frame {i}')
            if i<F['point'] or i>=F['standard']-12:
                old=cv2.resize(scene(i),(1080,1920),interpolation=cv2.INTER_LANCZOS4).tobytes()
            e.stdin.write(old)
            if i%600==0:print(f'{i}/{N}',flush=True)
        assert d.stdout.read(1)==b''
        e.stdin.close()
        if d.wait() or e.wait():raise RuntimeError('Final encode failed')
    # This separate public cut leaves the opener and loop free of text, and credits the actual map.
    font=v1.DATA/'Manrope.ttf'; text=v1.DATA/'map-credit.txt';text.write_text(OSM+'\nopenstreetmap.org/copyright',encoding='utf-8')
    vf=f"drawtext=fontfile='{font}':textfile='{text}':fontsize=23:fontcolor=white:x=66:y=252:line_spacing=3:box=1:boxcolor=0x081c2c@0.87:boxborderw=10:enable='gte(n,{START_CREDIT})*lt(n,{END_CREDIT})'"
    subprocess.run([FF,'-y','-v','error','-i',str(dest),'-vf',vf,'-filter_threads','1',*ENCODE,'-c:a','copy',*COMMON,str(pub)],check=True)
    print(dest,pub,sep='\n',flush=True)

if __name__=='__main__':main()
