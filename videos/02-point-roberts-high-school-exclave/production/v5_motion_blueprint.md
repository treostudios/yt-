# The Border Bus · V5 choreography blueprint

**Scope:** Revise the opening, the two location reveals, and the loop. Keep the V4 narration verbatim except for the completed ending. Keep its route geometry, measured bay comparison, crossing logic, treaty sequence and algebra payoff. **This is a production plan, not a V5 render.** The [V4 master](../final_short_v4.mp4) remains the review reference.

[Revised master script](v5_master_script.txt) · [60 fps choreography targets](v5_motion_cues.json) · [V4 audio and picture reference](v4_master_cues.json)

**Format:** 1080 × 1920, 60 fps CFR, 48 kHz stereo. Plan for about **51 seconds**; derive the final frame count from the recorded closer rather than squeezing the new words into V4’s 50-second file. Existing word landmarks below are from the V4 assembled dialogue. New closing landmarks are provisional.

## 1. Opening: descend to the bus, then rise into the map

**The first frame must already show a moving yellow school bus.** Don’t spend the first second finding it in an overhead map. The bus establishes the story; the climb reveals the geography.

| Output target | Narration anchor | Camera and action | Sound and text |
| --- | --- | --- | --- |
| **0–24f · 0:00–0:00.42** | “Every morning” | Start in a shallow aerial three-quarter view, roughly 10–14 m above Tyee Drive, with the moving bus already readable. Push in along the road and begin dropping on the outside of the lane. Dawn-side light rakes across the roof and asphalt; the vehicle shadow is attached to the road. | VO first; low tire roll already in motion. No intro sting or full-screen title. |
| **25–74f · 0:00.42–0:01.25** | “this American…” | Ease to a 1.6–2.0 m lens height; arc toward the side with a 75–85° viewing angle off the bus heading. Track independently of the bus body so the road and roadside move behind it while the windows remain readable. | Keep open space for the captions. A short, restrained airflow swell follows the descent, not the dialogue. |
| **75–122f · 0:01.25–0:02.05** | “…school bus” · V4 **bus ≈101f** | Hold an actual side-profile read. Reveal 3–4 minimalist stick-figure students through the near-side windows: simple eyes, small matching uniform collars, backpack straps and one bright pack visible within the cabin. One student glances toward the window; the others stay seated. Keep the characters behind the glass and window mullions. The bus, not the children, is the foreground subject. | No kid dialogue or cartoon squeaks. A subtle suspension or tire texture is enough. Keep “school bus” legible in the subtitle without laying type across the windows. |
| **123–179f · 0:02.05–0:03.00** | “has to drive through…” | Crane out of the side track, rotate the aim toward the lane ahead, then pitch down as the road opens into the peninsula. Keep the bus center and its road tangent registered across the lift. The detailed street props fall away with altitude; the bus becomes a readable map-scale icon only after its windows are too small to read. | Tire texture recedes while the same quiet coastal bed continues. No cut, white flash, or unrelated aerial shot. |
| **180–311f · 0:03.00–0:05.20** | “Canada… just to stay in the same state” | On **“Canada” (~180f)**, the already visible receiving side lights in muted crimson-slate. This is a preview, not crossing #1. Widen on **“same” (~261f)**; Point Roberts and Blaine show the same `WA` label while retaining their two focus colors. The real route casing makes the Canada detour readable. | One subtle border-reveal accent; no crossing stamp or counter. Let the map demonstrate the contradiction rather than adding explanatory VO. |

### Build the street-to-map handoff as a scale change, not a dissolve between locations

- Use a **true perspective street insert**: road mesh draped on the local terrain, modest curb/shoulder detail, a modeled American yellow bus with rolling wheels and glass, and a small interior rig. V4’s pitched heightfield and top-down sprite alone cannot do an eye-level side-profile pass. The street dressing and student figures are illustrative, not depictions of identified students, uniforms required by this school, or a verified bus model.
- Use the archived outbound approach as the common anchor. Build the street set in local metric coordinates, reference its tangent and elevation to the same mapped public road, and drive the hero and map bus from the **same chainage** through the scale change. Ground-contact height comes from the road surface; wheel spin follows distance. A road-level version of this shot cannot use V4’s accelerated map-scale travel speed. Start near a controlled approach patch, play the side track at a plausible road speed, and ramp simulated distance only after the ascent reads as geographic time compression.
- Render the low-altitude orbit with a true 3D perspective camera, then blend the near and regional levels of detail over a **registered overlap** out of the eye-level range. Match lens, road centerline, heading and screen position in that overlap; switch bus LOD behind its own matched roof silhouette. Coastline and border stay fixed in world space. Compress the scale climb with coordinated dolly and field-of-view, not a hard zoom that leaves the bus behind. Treat street → map as one camera move even if rendered in two passes.
- At phone size, check that the yellow body, two wheels and at least two students with backpacks read during the uninterrupted side-angle hold. If they don’t, improve framing or simplify silhouettes rather than stalling the hook.

## 2. Isolate one territory at a time

For focus, use **different accent colors but the same legal jurisdiction label**. Two glowing Washington surfaces must never read as two states or countries. Keep base imagery shaded and quiet; preserve the high-contrast land boundary as its own layer.

| Region | Accent treatment | Label |
| --- | --- | --- |
| Point Roberts | Cyan **`#40F4D5`**, light core **`#D5FFF6`**, pale emerald surface accent above the warm U.S. terrain. | `POINT ROBERTS, WA` |
| Mainland Washington / Blaine | Cobalt **`#496BFF`** with periwinkle edge **`#B5C5FF`**. Give the campus pin a light center so it does not merge with the blue ocean. | `BLAINE HIGH SCHOOL` · `WASHINGTON` |
| British Columbia | Crimson-slate **`#704F60`** applied as a low-saturation tint over relief, pale warm-gray text. No neon Canada fill during either focus beat. | `BRITISH COLUMBIA · CANADA` |
| Water | Deep navy/teal **`#082133` → `#123746`**, never the cobalt of mainland Washington. Retain the established red measurement stroke. | `BOUNDARY BAY` on the wide reveal |

| Target window / spoken cue | Blocking and timed response |
| --- | --- |
| **312–366f · “Point Roberts is right…”** | Track west into a **7–9 km** north-up framing target. Keep the entire Point Roberts land-boundary segment in frame, with air on both ends. Mainland Blaine and its pin must be **physically outside** picture at the hit, not merely hidden behind a label. Keep the Canadian side north of the line present but dim. |
| **367f · “here”** | Put a bright cyan-white core on the **actual Point Roberts land boundary on the cue frame**. Clip the cyan wash to the U.S. tip polygon; ring and coordinate leader originate at the chosen Point Roberts locator, not mid-water. Hold the core briefly; decay the bloom over ~12–18 frames. This is location #1, not a checkpoint transition. |
| **~391–482f · “Blaine High is right over…”** | Ease off the west close-up as “Blaine High” begins. Travel east over the registered bay in the same camera; intermediate travel may briefly show both coasts. Descend into a **5–7 km** destination framing target around the campus and the adjacent U.S. land. Point Roberts and its tag must be **offscreen** before the destination hit. Do not trigger a premature school pulse on the place name. |
| **483f · “there”** | Pop a bright periwinkle-edged cobalt pin locked to the Blaine High campus coordinates. Simultaneously reveal cobalt emphasis clipped to mainland Washington **on land only**. Use a different pin silhouette from the Point Roberts locator. Keep the border tick sound distinct from the campus click. |
| **~492–571f · “eleven miles across the bay”** | Pull back to **32–35 km** with both territories visible. By **“eleven” (~521f)**, the two measured shoreline endpoints should already be framed. Keep the two WA labels and muted BC readable in the same composition. Give the existing red dash head clear water to traverse from **“across” (~571f)**, then X it on **“no” (~715f)**. Don’t draw between the school pin and the Point Roberts locator; the source measure is shore to shore. |

The land masks and campus marker share the map projection. Retain the V4 route disclosure, source credits and separate return geometry. Later cues stay locked to the unchanged stems unless the timeline is explicitly reconformed. Hook lighting changes should not alter the four-crossing count or port evidence.

## 3. Finish the sentence, then match the motion into frame zero

> Which means these kids clear armed customs four times every single day... on a standard yellow school bus.

**Voice:** Keep narrator identity **`voice-01`**, the same warm General American documentary baritone and dry timing. Reuse the conformed V4 stems up to the closing sentence. Re-read the **whole closing sentence** as one phrase with that same voice; don’t paste a separately read “school bus” onto the old “yellow.” The pause is after **“day,”** not after “yellow.” Read “on a standard yellow school bus” as one breath with a calm downward finish on **“bus.”** No rising inflection, wink, clipped /s/, added line or new audition. Preserve the existing return question ahead of it and match the V4 EQ, gain and room bed at the join.

1. **On “four,”** finish the crossing tally, using the actual recorded replacement onset rather than carrying over a guessed V4 frame. Keep crossing #4 on the homebound road intersection; if the new read moves the nearby timing, reconform the last drive curve and tick together without shifting the return to a different road.
2. **On “standard,”** begin the descent toward the Tyee Drive opening setup. This is a **next-morning visual match**, not a claim that the bus suddenly reversed direction on the completed return trip. After the return count resolves, use the broad view/road alignment to hand off back to the northbound framing; never show the southbound bus snapping or spinning in place.
3. **On “school bus,”** the yellow hero bus is already back in the opening three-quarter setup. On the final **“bus”** onset, the complete final caption and vehicle are readable together. Continue tracking through the final consonant and leave only a short floor of room tone afterward (~3–6 frames, measured by ear), with no black frame or reset sting.
4. **At the seam,** the final frame is **one motion step before frame zero**, not a frozen duplicate. Match lens, bus heading, screen scale, grade, road/car parallax, tire-roll phase, and camera velocity; use the same hero asset in both. Render the first and last shuttles as a single motion cache around the loop point. Continue tire/air texture across the seam with a short wrap blend on the **bed only**, leaving both words intact. At the cut, clear the old caption and introduce “Every morning,” on its actual onset. Audition once as a standalone file and twice as a seamless concatenation.

## Conform and approval gates

1. Lock the same-voice closing take first. Mark **“four,” “standard,” “school,” “bus,”** and the audible end of /s/ from the edited dry stem. Recalculate end frame from the new take and update any affected captions, count, motion and SFX. Existing timestamps are useful as anchors, not substitutes for checking the final mix.
2. Inspect exported frames immediately before and at **“here”** and **“there”**. Confirm the opposite endpoint is out of frame; the active pin/boundary must gain visible full-strength contrast immediately, not start a slow fade. Apply the 60 fps floor-to-frame policy from V4 to measured dialogue landmarks; align sound cues on the sample grid. No claim of literal millisecond certainty from a blueprint.
3. Review three consecutive copies of the assembled delivery, first muted and then with headphones. Check wheel direction, screen travel, caption changes and tire/air continuity across the actual MP4 seam. Re-export if the resumed frame hesitates or the preceding sentence doesn't sound complete. Studio replay performance remains a measurement, not a promise of the loop design.
