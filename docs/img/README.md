# Defense deck images

The cost-comparison slide (Slide 9, "Bill of materials") shows a product photo for each
system in Table 6.5. Drop three image files here with these exact names:

| File | Should show | Suggested source |
|------|-------------|------------------|
| `compare-thisstudy.jpg`   | Our built 3D-printed arm (a real photo of the prototype) | Your own photo |
| `compare-dobot.jpg`       | Dobot Magician Lite | Dobot official site / retailer listing |
| `compare-lewansoul.jpg`   | LEWANSOUL (Hiwonder) xArm 1S | LEWANSOUL/Hiwonder site / retailer listing |

Notes:
- Any web image format works if you keep the `.jpg` name, but real `.jpg`/`.png` is safest.
- Roughly square or landscape crops look best in the three side-by-side boxes.
- If a file is missing, the slide still renders — the box shows a small
  `[add img/compare-*.jpg]` placeholder instead of breaking.
- Keep a note of each photo's source URL for the caption / your defense Q&A.
- **These three comparison photos are already embedded inside `defense_deck.html`** (as base64),
  so the deck is self-contained. Replacing a file here does NOT update the deck until it's
  re-embedded — tell Claude to re-embed if you swap one.

## Live-demo screenshot slots (optional)

The 5 demo slides show a placeholder box until you drop in a screenshot. Add these to have a
visual fallback in case the live demo fails on the day:

| File | Screenshot of |
|------|---------------|
| `demo-ide.png`      | The IDE with its five tabs visible |
| `demo-program.png`  | The Program tab: blocks on the left, generated C++ on the right |
| `demo-train.png`    | The Train Model tab |
| `demo-launcher.png` | The launcher window (Doctor / Start IDE buttons) |

- If a slot is empty, the slide shows a dashed `[ switch to the live IDE · or add img/... ]` box —
  it never breaks, so you can present live without them.
- ⚠️ **Portability:** these demo slots load from this folder, so if you add screenshots and want the
  deck to stay a single sendable file, ask Claude to embed them (base64) like the comparison photos.
