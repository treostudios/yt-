"""Optional conform from the saved same-voice pickup; stores the reproducible render stems and timing."""
from pathlib import Path
import json,re,subprocess
from pocketsphinx import Decoder
from imageio_ffmpeg import get_ffmpeg_exe

p=Path(__file__).resolve().parent; ff=get_ffmpeg_exe(); v=p/'voice_v5'; v.mkdir(exist_ok=True)
a=json.loads((p/'v4_master_alignment.json').read_text()); src=Path('.cache/pr_data/v5-close.wav')
old=a['words']['f']; sr=a['sample_rate']; stop=old[9][2]+round(.052*sr); head=stop+round(.12*sr)
subprocess.run([ff,'-v','error','-y','-i',str(p/'voice_v4/f.flac'),'-af',f'atrim=end_sample={stop-a["clip_starts"]["f"]}',str(v/'return.flac')],check=True)
text=(p/'v5_master_script.txt').read_text().split('Which means these kids')[-1]; text='which means these kids'+text.lower(); words=re.findall(r"[a-z]+(?:'[a-z]+)?",text)
subprocess.run([ff,'-v','error','-y','-i',str(src),'-af','silenceremove=start_periods=1:start_duration=0:start_threshold=-48dB:start_silence=0.018,areverse,silenceremove=start_periods=1:start_duration=0:start_threshold=-49dB:start_silence=0.08,areverse,atempo=1.045,highpass=f=68','-ar','48000','-ac','1',str(v/'close.flac')],check=True)
def pcm(path,rate):return subprocess.check_output([ff,'-v','error','-i',str(path),'-ar',str(rate),'-ac','1','-f','s16le','-'])
d=Decoder(samprate=16000,loglevel='ERROR');d.set_align_text(' '.join(words));d.start_utt();d.process_raw(pcm(v/'close.flac',16000),full_utt=True);d.end_utt()
new=[(re.sub(r'\(\d+\)$','',w.word),head+w.start_frame*480,head+(w.end_frame+1)*480) for w in d.seg() if not w.word.startswith(('<','['))]
assert [w[0] for w in new]==words
end=head+len(pcm(v/'close.flac',48000))//2
frames=(max(end,new[-1][2]+int(.075*sr))+799)//800
assert 50*60<=frames<=53*60,frames
out=dict(a,words=dict(a['words'],f=old[:10]+new),close_start_sample=head,close_end_sample=end,end_frame=frames)
(p/'v5_alignment.json').write_text(json.dumps(out,indent=2)+'\n')
print('Closing clip starts / ends / length:',head/sr,end/sr,frames/60);print(new)
