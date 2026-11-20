# The Border Bus · V4 final production blueprint

**50.000 s · 1080 × 1920 · 60 fps · 3,000 frames.** This is the execution handoff for the operator's [polished master script](v4_master_script.txt), not the earlier V4 pitch. Spoken wording stays unchanged. Narrator is the same `voice-01` as V3, with new takes. Preserve the complete spoken opening, and use a picture-and-sound loop rather than a closing title card. The algebra payoff gets a deliberate pause; the narrator doesn't signal the joke.

[Video master](../final_short_v4.mp4) · [Captions](../final_captions_v4.srt) · [Actual cue and camera data](v4_master_cues.json) · [All 3,000 frames: camera, bus chainage, cue starts and caption ID](v4_frame_plan.csv) · [Word alignment](v4_master_alignment.json)

## Visual and audio run of show

All frame indices are zero-based. These are the output frames from the rendered performance, not aspirational script timings. See the cue JSON for every hit and audio-sample position.

| Frames | VO anchors | Design, movement and sound |
| --- | --- | --- |
| 0–311 | “Every morning … same state” | Already rolling on Tyee Drive at frame zero. Amber bus and projected road line over shaded relief. First-frame `WASHINGTON → CANADA → WASHINGTON` shows the contradiction while the natural full sentence unfolds. At **180** the Canadian side responds to “Canada”; at **261** the two Washington endpoints light together. Coastal bed carries the cold open without a sting or lead-in. |
| 312–520 | “Point Roberts is right here. Blaine High is right over there.” | Camera begins moving on the place names. **367**: the entire displayed Point Roberts land span gains a mint core and glow, with a locator pulse and coordinates; dry click. **483**: the campus marker lands at Blaine High with a separate higher click. The camera movement leads the word; the flare or pin starts on it. |
| 521–774 | “Eleven miles across the bay. Nice shortcut. Shame there's no bridge.” | Distance tag and west endpoint appear on **521**; dashed red line sweeps east on **571** and completes before “shortcut.” At **715**, “no” places a red X and switches to `NO BRIDGE · NOT A FERRY ROUTE`; the gold road trace runs around the bay. Single lower click. |
| 775–1441 | “So why … in 1846 … snipping off this tiny peninsula tip.” | Sweep west; trace and pulse the peninsula perimeter. **928**: 1846 and Oregon Treaty. **1055**: draw head moves west along the actual mapped land segment. **1113**: historical `49° N` reference anchors the explanation. **1262**: snap the completed line and pulse the tip on “snipping”; land doesn't physically detach. |
| 1442–1699 | “The only road out … foreign country. So the bus crosses here.” | Follow the only public connection from Tyee Drive onto 56 Street. Expose Canada on **1550**. Show a short illustrative stop on the approach, then move onto modeled crossing at **1675**: bus, `01`, ring, and crossing tick from the same marker. No inspection lane or procedure is asserted. |
| 1700–1990 | “Loops twenty-six miles through British Columbia … back into the U.S. at Blaine.” | Rise and track the real bends; reveal `≈26 MI · BC-17 → BC-99` with highway labels anchored to the mapped example. Camera closes on the mainland port. At **1906** (“U.S.”), road intersection, `02` and second tick; the **1955** Blaine marker starts the school approach, which ends on the public campus-area road. |
| 1991–2326 | “Two international borders. Forty minutes. And the prize at the end? Algebra.” | Card clarifies `2 CROSSINGS · ONE WAY`, then shows `≈40 MIN / REPORTED ONE WAY`. At **2146** the reward card unfolds. The question ends just before 36.84 s. At **2240** (`37.338 s` audio marker), drop the worksheet `SOLVE FOR x` with one paper snap. Let the card sit; no laugh sting. |
| 2327–2734 | “After school? They do the entire international commute in reverse. Which means these kids clear armed customs …” | School bell partial starts the distinct homebound trace. At **2416** and **2699**, the bus reaches crossings `03` and `04` respectively. Each tick, badge and glowing road intersection shares that return event. No weapon, queue or customs procedure is depicted. |
| 2735–2999 | “Four times every single day … on a standard yellow …” | `4 BORDER CROSSINGS / PER SCHOOL DAY` appears on “four”; travel and summary resolve before the camera returns to the opening Tyee Drive pose. The yellow bus **visually supplies the unfinished noun**. No extra spoken word; the next playback starts “Every morning.” The ambient bed wraps. This is a picture-led loop: “yellow” and “Every” are intentionally not presented as a grammatical sentence. |

## Sync, map and QA notes

- The six narration takes are trimmed in speech gaps and gently tightened without changing pitch. The stored FLAC stems are the conformed takes used in the mix. Speech onsets were estimated from those edited stems with PocketSphinx forced alignment on a 10 ms grid. The renderer displays hard hits on the containing 60 fps frame (up to 16.67 ms earlier than the estimated onset), with an immediately bright first frame rather than a delayed fade. The click/stamp can be set on the indexed mix sample; that number is not a guarantee that a human perception of the syllable starts at that millisecond.
- One shared heightfield camera with draped overlays handles continuous local and regional moves. The bus's position and heading come from the mapped road sample and tangent, not straight travel from pin to pin. [Archived direction-specific OSM road geometry and attribution](route_data/README.md) uses **Pacific Highway** for the mainland example and **Boundary Bay** for Point Roberts. [Regional directions and the approximate one-way drive](https://www.pointrobertschamberofcommerce.com/getting-here/) independently support the highway corridor and commute scale. The screen label **EXAMPLE DRIVE · DISTRICT ROUTE UNVERIFIED** distinguishes this from district records. Separate homebound geometry is used; the instrumented stops do not show real lines or inspection procedures.
- The red water span is **17.889 km / 11.116 mi** between shorelines, not to the school, not a ferry line, and not compared as a matched-endpoint driving distance. The gold example road route is approximately **26 mi** in total, not a claim that every mile is in British Columbia. The travel time is a reported approximation, not a model prediction.
- Script interpretation: “two international borders” means **two crossings of the same international boundary**, and “every single day” refers to **school days**. The Oregon Treaty established the boundary in this area; the graphic does not claim documentary proof that the outcome was an accident. The supplied “armed customs” phrasing stays in the VO; the video does not make an independent claim about officers' equipment at any moment.
- Keep the visual loop and full-sentence hook as standing creative defaults. Measure impact in Studio rather than inferring 120% APV from the edit. At 50 seconds, 120% APV is 60 seconds of average view duration.

## Rebuild

After the [common production setup](README.md), from the repository root:

```sh
D=videos/02-point-roberts-high-school-exclave/production
python "$D/export_master_v4_cues.py"
python "$D/render_master_v4.py" --samples # optional review frames
python "$D/render_master_v4.py"
```

Rebuild uses stored stems and does not regenerate speech or require an external aligner. `align_master_v4.py` documents the optional alignment pass for the original six raw audition-service reads (`v4-a.wav` through `v4-f.wav` in the ignored cache); install `pocketsphinx` only to rerun that step. The prior V1/V2/V3 masters remain intact. No upload was performed.

**Delivery check:** Full decode of 3,000 Rec.709 H.264 frames and 48 kHz stereo AAC; mix measured −14.1 LUFS integrated and −1.3 dBTP. Pre-hit/hit export frame pairs checked for the peninsula, campus pin, red X, both outbound crossings, the algebra card, and the final return crossing. The last and first exported pictures share the map and bus pose; the opening caption enters on the reset.
