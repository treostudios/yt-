# The Border Bus · V5 rendered handoff

[50.35-second master](../final_short_v5.mp4) · [Caption file](../final_captions_v5.srt) · [Thumbnail reference](../thumbnail_frame_v5.jpg) · [Conformed cue sheet](v5_conformed_cues.json) · [Approved script](v5_master_script.txt) · [Choreography blueprint](v5_motion_blueprint.md)

## What was rendered

- **Street opening:** A software-rendered perspective set and bus mesh, not an enlarged map icon. The camera starts above the moving bus, drops to a near-eye-level side track, then swings overhead and lifts into the shaded-relief map. The bus windows use a stylized interior material with animated student expressions, uniform collars and backpacks. The street vignette illustrates a local road view; its scenery, students and vehicle aren't documentary reconstructions. The lift uses registered road progression and a blended change of scale between the illustrative street set and the geographic map.
- **Location contrast:** At **frame 367 (6.117 s)**, the Point Roberts land boundary flashes cyan and a cyan wash is clipped to the tip. At **frame 483 (8.050 s)**, the Blaine High pin hits and contiguous mainland Washington gains cobalt shading. The opposite location is out of frame on each hit. Both are labeled Washington in the wider composition; British Columbia stays subdued. The red bay span still measures **shore to shore**, not to the campus or along a ferry route.
- **Completed loop:** A new performance of the complete closing sentence uses the same `voice-01`. The existing performance remains through “in reverse.” The last subtitle ends **“yellow school bus.”** The final **“bus”** begins near frame **2990 (49.833 s)**; the full consonant tail plays through before replay. The street rig evaluates continuous negative/positive time across the first and last frame, preserving bus track, heading and wheel phase. The tire/air bed wraps without wrapping or truncating VO. The return to Tyee Drive is a visual match, not a literal time-continuous U-turn.
- The V4 midsection remains substantially intact: actual direction-specific public-road geometry, conservative **example-drive** disclosure, measured water comparison, treaty line, and algebra prop. The final count and return intersection were reconformed to the pickup so the road hit and cue are driven together.

| Cue | 60 fps output frame (zero-based) |
| --- | ---: |
| Side-profile school bus, “bus” | 101 |
| Same-state regional reveal | 261 |
| Point Roberts hard hit | 367 |
| Blaine High hard hit | 483 |
| Crossings 1, 2, 3, 4 | 1675, 1906, 2416, 2701 |
| “Four” count | 2737 |
| Final “school” / “bus” | 2973 / 2990 |
| Final picture | 3020 |

All hits are based on the stored word-alignment estimates, rendered to the containing video frame rather than timed to subtitle block starts. The wrap does not add a freeze or a fade to black. Nothing was uploaded to YouTube.

## Rebuild

From the root, after the shared [map asset setup](README.md#rebuild):

```sh
D=videos/02-point-roberts-high-school-exclave/production
python "$D/render_master_v5.py" --samples  # optional review frames
python "$D/render_master_v5.py"            # final MP4 and cue exports
```

The stored stems and alignment remove the need to regenerate speech to rebuild. `conform_v5.py` is the optional one-time edit/alignment pass; it expects the raw same-voice closing take in the ignored cache and PocketSphinx. The V4 path of the shared renderer remains unchanged when its defaults are used.

**Export checks:** 50.350 s, all 3,021 frames decoded, 1080 × 1920 at 60 fps, Rec.709 H.264 and stereo 48 kHz AAC. Measured −14.1 LUFS integrated / −1.3 dBTP. Checked decoded frames on both sides of the two location hits and the last return crossing, plus the opening, street-to-map lift and final/first frame pair. Audio is trimmed to the picture duration so encoder/filter padding cannot lengthen the loop.
