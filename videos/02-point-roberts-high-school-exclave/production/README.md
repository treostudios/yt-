# Point Roberts · final production handoff

- [Final Short](../final_short.mp4) · 55 seconds, 1080×1920 delivery, 30 fps CFR, H.264 / AAC stereo, Rec.709, web-optimized MP4.
- [Final captions](../final_captions.srt) · timed to the rendered narration; the master also has burned-in captions. [Final timeline](../final_timeline.json) · edit cues and camera keyframes. [Thumbnail reference](../thumbnail_frame.jpg) · select the actual frame near 00:02.500 in the Shorts upload interface.
- Full program decode completed: 1,650 frames; AAC at 48 kHz stereo; −14.1 LUFS integrated and −1.2 dBTP measured from the rendered audio. No platform upload was performed.
- Original 26-second files and the 55-second scratch board are retained for comparison. Use the `final_` timeline and captions for this master.

## Creative and data decisions

The topic positions the story for a U.S. and Canadian geography audience through the subject itself, with a school-day hook that's understandable elsewhere. Country distribution is a Studio measurement, not a setting encoded in the edit. The render uses the General American audition fallback; nobody selected it as their preferred narrator. The six isolated synthesized voice clips are in `voice/`, separate from the procedural bed, crossing ticks, whooshes, and school bell. The narrator keeps the boat line dry. The stylized late slip is an illustration, not a claimed school document or actual lateness.

This is a custom Python/OpenCV cartographic render, not a proprietary GEOlayers project. The north-up map uses a local metric approximation, stylized relief, and a generalized **land** boundary; no imaginary straight line over water is used as a legal boundary. The bus symbol follows the public Point Roberts approach, not a pickup or published inspection lane. The remaining route is a country-transition schematic; no exact district itinerary, Blaine port or real-time crossing duration is claimed. Reported travel time is an estimate, not a timetable.

### Credits to include with the upload

- Point Roberts detail and public roads: [© OpenStreetMap contributors](https://www.openstreetmap.org/copyright), ODbL, as cached by the [Point Roberts Ocean View project](https://github.com/johnpoole/PointRobertsOceanView/tree/1a4a328a1dc642cf82ac691116fcd2cd1ca5a77e).
- Regional shoreline: [GSHHG](https://www.soest.hawaii.edu/pwessel/gshhg/), Paul Wessel and Walter H. F. Smith, via `basemap-data-hires`. Country geometry reference: [Natural Earth](https://www.naturalearthdata.com/about/terms-of-use/) (public domain).
- Shaded terrain: NOAA NCEI [CUDEM](https://www.ncei.noaa.gov/products/coastal-elevation-models), and [Global Multi-Resolution Topography (GMRT) Synthesis](https://www.gmrt.org/about/terms_of_use.php), Ryan et al. (2009), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), resampled and shaded; cached terrain inputs via the same Point Roberts project.
- Typeface: [Manrope](https://github.com/google/fonts/tree/main/ofl/manrope), SIL Open Font License 1.1.
- Story: [Oregon Treaty, Article I](https://web.archive.org/web/20050113095649/http:/www.lexum.umontreal.ca/ca_us/en/cus.1846.28.en.html), [Blaine High School](https://www.blainesd.org/o/blaine-high-school/), [Seattle Times](https://archive.seattletimes.com/archive/?date=20050613&slug=pointroberts13m), and [Atlas Obscura](https://www.atlasobscura.com/places/point-roberts).

## Rebuild

From the repository root, with Python 3.11, your system's `curl`, and a virtual environment:

```sh
D=videos/02-point-roberts-high-school-exclave/production
python -m pip install -r "$D/requirements.txt"
bash "$D/fetch_assets.sh"
python "$D/render.py"
```

`--samples` writes preview stills to `.cache/pr_data/`. Sources, the basemap cache, and temporary mix stay out of version control. If replacing the narrator, conform the shot cues and caption timing to the new read before rebuilding. The voice files and rendered deliverable are retained here because they are production assets.
