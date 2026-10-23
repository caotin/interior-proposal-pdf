# HTML export and verification

## Dependencies

Use available workspace runtimes or install project-local dependencies: Node.js 20+, Python 3.10+, Playwright with Chromium, pypdf, and Poppler (`pdfinfo`, `pdftoppm`). Python's standard library is sufficient for quotation checking. PyYAML is needed for repository skill validation.

`render_pdf.mjs` resolves Playwright through `--node-modules`, `NODE_PATH`, or normal Node module resolution. Chromium must be installed separately using Playwright, or select existing Chrome with `--executable`. Local HTML serving binds only to loopback; restricted hosts may require execution approval for the browser/server.

## Portable fonts and assets

Keep CSS, images, and fonts beneath the HTML directory. The default starter uses system serif/sans fonts; for portable typography, supply locally licensed fonts using `@font-face` and retain their licenses. Check target-language glyphs in the exported PDF. Do not redistribute commercial operating-system fonts without permission.

The six-page example includes Noto Sans/Serif and their supplied license notices. Its document language is Vietnamese to demonstrate diacritic support; skill instructions and repository documentation are English.

## Page contract

```html
<section class="page" data-page-id="product-01">
  <main class="safe" data-safe-area>...</main>
  <footer class="folio"><span>Project name</span><span>04</span></footer>
</section>
```

Set `@page { size: 1280px 720px; margin: 0; }` and matching `.page` dimensions. Change both together for other formats. Break after each page except the last. Remove screen margins/shadows in print media. Full-bleed imagery may touch edges; body text belongs inside `.safe`, and folios have their own position.

`.safe` is absolutely positioned using `inset`. Do not give it `height: 100%`, which overrides the intended bottom inset and can overflow. Likewise, a child grid below a heading must fit the **remaining** content height, not the whole page.

The renderer serves authored, static HTML from a temporary loopback origin and blocks external requests. Do not embed untrusted scripts from supplied reference material. It is an export tool for trusted author-created HTML, not a general sandbox for hostile webpages.

## Automatic checks and their limits

The renderer checks unique page IDs, consistent page geometry, print gaps, loaded images/fonts, text extending outside page/safe boundaries, scrolling/clipped text containers, failed requests, and browser errors. It exports only after preflight passes and can capture per-page HTML screenshots.

These checks do not prove attractive crops, correct pricing, complete glyph coverage, or the absence of every possible overlap. Review PDF renders and extract text independently. If a previous PDF already exists, a failed render leaves it unchanged; always check the new report and successful exit status before delivering a file.

## After export

```bash
pdfinfo project/proposal.pdf
pdftoppm -scale-to 1600 -png project/proposal.pdf project/qa/pdf-page
```

With pypdf, compare page count against `render-report.json`, check page sizes within approximately 0.2 pt, require non-empty pages, and inspect extracted language-specific text, item IDs, and final prices. A nonzero PDF file size is insufficient verification.

PDF extraction can insert spaces between tracked letters and return decomposed Unicode accents. Normalize Unicode composition and extraction-added whitespace when matching expected text; retain the original extraction for diagnosis. Do not interpret extractor spacing alone as a visual layout defect.

Use a contact sheet for document rhythm and navigation. Inspect readable PDF renders for each distinct layout and every suspicious page, and review new renders after corrections. QA notes should state the actual pages reviewed, remaining unknowns, and image-resolution limits.

## Deliverable layout

```text
project/
  proposal.pdf
  proposal.html
  print.css
  assets/images/...
  assets/fonts/...       # where redistribution is permitted
  content.md
  page-plan.md
  design-brief.md
  quote.json            # when quoting prices
  image-manifest.json
  qa/render-report.json
  qa/quote-report.json
```

Remove unfinished scaffolding and broken assets before calling a deliverable final. Clearly label hypothetical data and unresolved drafts. Use relative resource paths so the source bundle can be opened and exported elsewhere.
