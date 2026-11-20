"""Conform the six speech-generation takes to a sample-addressable master."""
import subprocess,json,re,wave
from pathlib import Path
import numpy as np
from pocketsphinx import Decoder
from imageio_ffmpeg import get_ffmpeg_exe
D=Path('.cache/pr_data'); f=get_ffmpeg_exe()
texts=["Every morning this American school bus has to drive through Canada just to stay in the same state", "Point Roberts is right here Blaine High is right over there It's eleven miles across the bay Nice shortcut Shame there's no bridge", "So why does Washington have a piece stuck over here In eighteen forty six diplomats drew the forty ninth parallel straight across the map accidentally snipping off this tiny peninsula tip Which means the only road out leads straight into a foreign country", "So the bus crosses here loops twenty six miles through British Columbia and crosses back into the U S at Blaine Two international borders Forty minutes And the prize at the end", "Algebra", "After school They do the entire international commute in reverse Which means these kids clear armed customs four times every single day on a standard yellow"]
P=Path(__file__).resolve().parent; VO=P/'voice_v4'; VO.mkdir(exist_ok=True)
# Edit only measured gaps between words. Preserve the dramatic algebra stop.
edits=[[(0,3.76),(4.13,5.77)],[(0,1.35),(1.56,3.69),(4.07,6.13),(6.47,7.47),(8.05,9.36)],[(0,2.76),(3.95,12.35),(12.92,14.42),(14.87,17.27)],[(0,6.51),(6.98,8.60),(8.77,9.75),(10.37,11.72)],[(0,.78)],[(0,.83),(1.32,4.64),(5.1,10.74),(11.35,13.15)]]
starts=[]; allwords={}; head=640
for k,text,cuts in zip('abcdef',texts,edits):
 src=D/f'v4-{k}.wav'
 cmd=[f,'-v','error','-y','-i',str(src)]
 parts=';'.join(f'[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS[x{i}]' for i,(a,b) in enumerate(cuts))
 names=''.join(f'[x{i}]' for i in range(len(cuts)))
 # Keep native timbre and only modestly tighten overall delivery.
 rate=1.06 if k!='e' else 1
 dst=VO/(k+'.flac'); subprocess.run(cmd+['-filter_complex',f'{parts};{names}concat=n={len(cuts)}:v=0:a=1,atempo={rate},highpass=f=68','-ar','48000','-ac','1',str(dst)],check=True)
 d=Decoder(samprate=16000,loglevel='ERROR'); d.add_word('snipping','S N IH P IH NG');d.set_align_text(text.lower()); raw=subprocess.check_output([f,'-v','error','-i',str(dst),'-ar','16000','-ac','1','-f','s16le','-']);d.start_utt();d.process_raw(raw,full_utt=True);d.end_utt()
 starts.append(head)
 words=[(re.sub(r'\(\d+\)$','',w.word),head+w.start_frame*480,head+(w.end_frame+1)*480) for w in d.seg() if not w.word.startswith(('<','['))]
 assert [w[0] for w in words]==text.lower().split()
 allwords[k]=words
 n=len(subprocess.check_output([f,'-v','error','-i',str(dst),'-ar','48000','-ac','1','-f','s16le','-']))//2
 head+=n+round(48000*{'a':.09,'b':.10,'c':.055,'d':.50,'e':.68,'f':.12}[k]);print(k,words[0],words[-1],n/48000)
assert head<55*48000,head/48000
(P/'v4_master_alignment.json').write_text(json.dumps(dict(sample_rate=48000,analysis_hop_ms=10,clip_starts=dict(zip('abcdef',starts)),end_sample=head,words=allwords),indent=2)+'\n')
