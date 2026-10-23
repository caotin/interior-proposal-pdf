# Consistent imagery at document scale

## Plan the image inventory

Use one manifest record per image. Inspect the current image tool's schema; do not assume it exposes seeds, batch generation, or a selectable output path.

```json
{
  "style": "Japandi, ivory linen, light oak, olive accents, warm daylight",
  "images": [
    {
      "id": "living-hero-01",
      "role": "room",
      "page_ids": ["cover", "living-overview"],
      "item_ids": ["01"],
      "aspect_ratio": "16:9",
      "prompt": "Architectural visualization ... no typography or logos",
      "reference_ids": [],
      "source": "ai-generated",
      "status": "planned",
      "local_path": null,
      "review_notes": null
    }
  ]
}
```

Advance through `planned → generated → reviewed → placed`. Mark a failed candidate `retry` and record the reason; keep previous candidates rather than regenerating blindly. `local_path` must identify an actual file in the portable HTML bundle. Record whether imagery was supplied, licensed, or generated. Do not describe AI concept images as photographs of completed work.

## Generate, review, and place

1. Generate one reviewed anchor scene for each distinct room design using a shared palette.
2. Inspect materials, furniture geometry, perspective, lighting, object counts, and space for copy.
3. Use the anchor as an image reference for additional views or isolated products. Pass real local paths or the tool's supported conversation-image mechanism; do not replace a fidelity-sensitive edit with a text-only request.
4. For products, retain silhouette, upholstery, material, base, and proportions. Use a warm neutral studio background and a complete three-quarter view. Compare the result against the room scene. Prefer supplied product photography when manufacturing accuracy matters.
5. Make material swatches and detail images from relevant crops where possible; generate separate studies where crops are insufficient.
6. Copy tool outputs into `assets/images/` with stable ID-based filenames. Use native tool image display where applicable, and never dump base64 into conversation output.

Work through room and product IDs, saving the manifest after every result, until every image slot in the page plan is satisfied. There is no fixed image-count cap. Reuse approved images intentionally; a document with many different rooms/products generally requires many distinct images.

After three unsuccessful attempts at the same image, reassess its prompt/reference, adapt the layout, or identify the unresolved asset. Report quota/tool failures accurately and preserve resumable state.

## Adaptable prompts

**Room:** “Architectural interior visualization of [space and layout], [materials and approved furniture], consistent with reference [ID], [camera angle], [lighting], restrained editorial aesthetic, plausible buildable proportions, [aspect ratio], no text, labels, watermark, dimensions or logo.”

**Product:** “Using the supplied room reference, isolate the exact [item], preserve [silhouette, upholstery, base, material], full object in frame with generous margins, three-quarter studio product photograph, warm neutral seamless background, soft contact shadow, no added accessories, typography, labels or dimensions.”

**Material:** “Close material study of [verified material], realistic [grain/weave/finish], diffuse light, flat editorial swatch, no text or invented certification marks.”

Do not generate dimensioned technical floor plans as factual drawings. Place annotations, captions, item IDs, and prices as HTML/vector elements.

## Resolution

For a 960 × 540 pt PDF, a 1920–2560 px room image is often suitable for screen use. Physical printing requires checking actual page dimensions and requested DPI: a 1280 px image across a 13.33-inch page is about 96 dpi. Do not claim 300 dpi without adequate source pixels or disguise missing detail by upscaling.
