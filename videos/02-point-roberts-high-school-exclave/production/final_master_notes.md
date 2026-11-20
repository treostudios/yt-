# The Border Bus · final finishing master

- **[Clean master](../final_short_master.mp4):** no burned-in attribution or metadata strip anywhere in the frame. Captions and explanatory labels remain. Keep this as the editorial master.
- **[YouTube upload copy](../final_short_publish.mp4):** same edit, with one four-second, readable map credit during the road-map sequence (frames 1700–1939; 28.333–32.333 s). Both the opening and the loop are clean. Publish with the [description and source credits](../upload_pack.md#description); the clean picture version is not the recommended upload for this map-led video. The [OpenStreetMap Foundation video guideline](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines#TV.2C_film.2C_or_video_productions) recommends a visible map credit when the map is a major component. Full [production credits](README.md#credits-to-include-with-the-upload) and MP4 source metadata are retained for both exports.
- **[Captions](../final_captions_v5.srt)** · **[Thumbnail reference](../thumbnail_frame_final.jpg)** · **[Conformed cue sheet](v5_conformed_cues.json)**. Reuse the approved V5 timebase, with no cue or caption retiming.

## Finishing changes

1. **Roadside foliage:** replaced the simple single-cone stand-ins with layered, faceted evergreen meshes. Staggered branch tiers, trunk geometry, fixed contact shadows and directional colors stay consistent across the street-to-map move and both sides of the loop. The camera-side shoulder remains clear enough to read the students and backpacks through the bus windows. Bus and camera paths stayed fixed.
2. **“Algebra.”** Recorded new takes with `voice-01`, selected the contextual read with a reduced middle vowel, and isolated only the word. The stem targets North American **/ˈæl.dʒə.brə/**, with the emphasis on “AL.” Matched the short beat and level to the original delivery. The take is placed at the same sample as V5 (frame 2240), so the question, pause, paper snap, and `SOLVE FOR x` reveal retain their timing. No other dialogue stem was replaced.
3. **Clean canvas:** removed the V5 opening/closing credit overlay at its source, not with a crop or cover-up. The upload copy instead carries the map credit while the public road example is on screen; it does not introduce a separate end card.

The street set remains illustrative. Location flashes, shore-to-shore comparison, distance labels, exact caption windows, route and border intersection cues, end line and final/first camera match are carried over from V5.

## Rebuild

After restoring the [shared map assets](README.md#rebuild), run from the root:

```sh
D=videos/02-point-roberts-high-school-exclave/production
python "$D/render_final.py" --samples   # optional street and loop frames
python "$D/render_final.py"            # clean and credited MP4s
```

The pass uses the stored V5 picture for unchanged frames and re-renders only the bookends. The checked-in isolated pickup is `voice_final/algebra.flac`; no speech service is needed to rebuild. Neither version has been uploaded to YouTube.

**Delivery QC:** Both exports decoded all **3,021 frames** at **1080 × 1920, 60 fps**, total duration **50.35 s**, with Rec.709 H.264 and 48 kHz stereo AAC. Final audio measured **−14.1 LUFS integrated / −1.3 dBTP**. Reviewed the opening swoop, side angle and closing matched frames, plus the credit placement in the upload copy. The original V5 master and voice stem are unchanged.
