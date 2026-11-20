# The Border Bus · V3 motion and source notes

[Watch the V3 master](../final_short_v3.mp4) · [Caption transcript](../final_captions.srt) · [V3 thumbnail frame](../thumbnail_frame_v3.jpg)

**Locked 55-second narration and cut length.** V3 retains the V2 region-to-local pitch/heightfield, then puts the transportation comparison and the moving bus directly on the geography. The route is an example based on real mapped public roads, not the district's verified itinerary. The captioned source audio and the two deadpan jokes are unchanged. No part of the map is presented as navigation guidance.

| Time | Spoken concept | V3 on-map execution |
| --- | --- | --- |
| 0:00–0:06 | School bus, leaving the country, high school in the same state | Continuous overview-to-local descent. The bus locator gives way to the heading-aware bus on Tyee Drive; a fine road casing previews the detour. Point Roberts and Blaine light together on the same-state reveal. |
| 0:06–0:12 | First stop, Canada; the only road out of Point Roberts | Crossing **01** pulses when the animated axle intersects the mapped boundary at Boundary Bay, about **0:07.57**. The pin and road leader stay with the geography as the camera rises. |
| 0:12–0:20 | Blaine is across Boundary Bay; the bus isn’t a boat | Cyan dashed measurement draws shoreline to shoreline; the distance grows with the line, then settles at **about 11 mi / 18 km**. It is labeled as a comparison, not a ferry route. The gold road trace responds on “not a boat,” with the **about 26 mi / 42 km** example-drive distance shown separately. |
| 0:20–0:31 | The tip, Oregon Treaty, 49th parallel, U.S. side | Cutaway within the same geographic rig: contour and fill point to the tip, the historical date resolves, and the light travels over the land boundary as it is named. The trip-progress clock pauses for this explanation and resumes from the same road chainage; no bus jump. |
| 0:31–0:37 | Driving through British Columbia, back into the U.S. at Blaine, pulls up at high school | Camera tracks the turning road-follow bus. Crossing **02** engages the Pacific Highway example boundary hit at **0:34.03**. Bus reaches the mapped public campus road; the distinct school pin pulses with the spoken destination. |
| 0:37–0:42 | About forty minutes; one way | Clock and directional tab unfold from the school anchor; the silent late slip replaces the clock with a dry paper tick. The reported commute estimate is not calculated from the illustrative road data. |
| 0:42–0:49 | Last bell; into Canada; back into Washington | Separate direction-specific return geometry, not a reversed graphic. The camera lifts, crosses the public corridor in compressed time, and re-enters Point Roberts. **03** at **0:46.80** and **04** at **0:48.63** have their own world-space hits. |
| 0:49–0:55 | Four crossings; own district | Sum emerges from the fourth crossing; both endpoints carry the school-district payoff, then the continuous rig returns to the opening locator. |

## Geography and source checks

- The route vertices are the archived [direction-specific OSRM responses](route_data/README.md) on OpenStreetMap road geometry. The example shows Pacific Highway and Boundary Bay. An on-screen disclosure stays with the driving demonstration: `EXAMPLE DRIVE · DISTRICT ROUTE UNVERIFIED`. The example has no student pickup points, real-time data, or assertion about actual school bus lanes or checkpoint procedures.
- Both polylines must decode and intersect the displayed boundary exactly twice. Intersection samples are sorted by driven chainage and tied to the cue-sheet frames 227, 1021, 1404, and 1459; the same frames trigger the four master-mix ticks. The route line and wheel/axle heading share the same position sample. No waypoint or road segment is interpolated over the bay.
- The dashed line starts at the Point Roberts east shoreline and ends at the first opposing mapped Blaine-area shoreline on the comparison bearing. Distance computed from the actual mapped end coordinates: **17.889 km / 11.116 mi** (spherical great-circle approximation). The water geometry is measured, not a suggested boat path, bridge, navigable channel, or existing ferry. It is not endpoint-to-campus, so the road and water readings should not be interpreted as identically sampled navigation distances.
- The animated boundary is based on the same local IBC-derived transcription and mapping limitations as V2. [Blaine High School](https://www.blainesd.org/o/blaine-high-school/) verifies the school location; [school commute reporting](https://archive.seattletimes.com/archive/?date=20050613&slug=pointroberts13m) supports the trip mechanics and reported estimate. Neither source establishes the exact port or road itinerary of the current district bus.

## Rebuild and QA

After the shared environment and asset setup in the [handoff](README.md), run `python "$D/render_v2.py" --v3` with `D` pointing to the production directory. Add `--samples` for frame stills. The master passed full decode: **1,650 frames**, **55.000 seconds**, 1080 × 1920 30 fps Rec.709 H.264 plus 48 kHz stereo AAC. Audio from the export measured **−14.1 LUFS integrated**, **−1.3 dBTP**. V1 and V2 MP4s remain unmodified.
