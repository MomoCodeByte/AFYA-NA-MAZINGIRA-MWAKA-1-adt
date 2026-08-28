# Afya na Mazingira - Page Conversion Checklist

Source PDF: `..\AFYA NA MAZINGIRA MWAKA 1.pdf`

Web mapping: PDF page N = web page N
Total pages: 72

| Page | Status | Notes |
|---:|---|---|
| 1 | visually checked | Semantic cover; approval certificate retained as a clean image crop; desktop/mobile checked. |
| 2 | visually checked | Semantic copyright and publication details; desktop/mobile checked. |
| 3 | visually checked | Semantic linked table of contents; destinations and desktop/mobile layouts checked. |
| 4 | visually checked | Semantic acknowledgements; handwritten signature retained as a clean image crop; desktop/mobile checked. |
| 5 | visually checked | Semantic introduction; Rehema read-aloud and timed word highlighting checked; desktop/mobile checked. |
| 6 | visually checked | Blank source page retained in the page mapping; printed folio and production metadata removed. |
| 7-13 | visually checked | Chapter 1 converted to positioned semantic HTML with text-free illustration artwork; exercises and table composition checked on desktop/mobile. |
| 14-23 | visually checked | Chapter 2 food, water, fruit, and exercise pages converted and compared with the PDF on desktop/mobile. |
| 24-47 | visually checked | Chapter 3 hygiene and disease pages converted; illustrations, answer spaces, boxes, and tables checked on desktop/mobile. |
| 48-60 | visually checked | Chapter 4 environment, safety, and road-sign pages converted and compared on desktop/mobile. |
| 61-65 | visually checked | Chapter 5 animal and plant pages converted and compared on desktop/mobile. |
| 66-72 | visually checked | Chapter 6 first-aid pages converted and compared on desktop/mobile; illustration-only narration and timed highlighting checked. |

Final audit: 72/72 pages use semantic HTML; no page uses a full-page screenshot or legacy PDF text layer. Rehema narration hooks are dedicated hidden elements, the intentional blank page 6 has no hook, and the mobile viewer toolbar exposes every accessibility control.

## Interactive exercise phase 1

- Removed the blue gradient edge decoration from every page and every reusable artwork layer.
- Added answer controls directly to the printed questions on 40 exercise pages, covering 146 manifest activities plus any remaining printed dotted or underscored blanks.
- Normal questions receive an answer line beside or immediately below their wording; printed blanks become interactive fields in their original positions.
- Supported controls: short text inputs, expandable text areas, multiple-choice radio options, True/False options, single-answer selectors, and matching selectors.
- Answers are saved automatically in the reader's local browser storage and restored when the page is reopened.
- Submit and result buttons are intentionally deferred to the next phase.
- Reflowed 23 densely printed exercise pages so every question and field occupies its own row inside the original exercise box; the page-72 arrangement supplied by the user was checked with zero field-to-text collisions, including while a field is focused.
- Restyled every answer control as a clear white writing area with a cyan outline, rounded corners, internal padding, and a readable placeholder. Long-answer questions have taller text areas instead of thin answer lines.
- On phones, controls remain proportional inside the printed page and expand into a readable 44-pixel input or 76-pixel text area when focused, above the viewer toolbar.
- Browser checks covered multiple-choice (page 9), matching (page 13), writing and printed-blank fields (pages 12, 47, 56, and 72), road-sign answers (page 60), True/False (page 56), answer persistence, and a non-exercise page (page 14). Pages 39 and 59 received final question-specific spacing corrections.
- Final browser audit covered all 40 interactive pages and 173 rendered controls at desktop width: zero controls outside the page, zero clipped reflow panels or rows, and zero contacts with visible printed text. The phone-width audit covered the same 40 pages with zero controls outside the page and zero panel or row overflow.
