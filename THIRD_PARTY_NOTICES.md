# Third-party notices

## Noto fonts

The example includes unmodified Noto Sans and Noto Serif font files. Their supplied license notices are preserved in [examples/riverside-living/assets/fonts/LICENSE.txt](examples/riverside-living/assets/fonts/LICENSE.txt). Font licensing is separate from this repository's MIT license. The font files retain embedded authorship/copyright metadata.

## Generated demonstration imagery

The two room/product images were generated with OpenAI ImageGen for this project. The [image manifest](examples/riverside-living/image-manifest.json) records the prompts, source type, reference relationships, and limitations. README illustrations are page renders of the fictional demo made from those assets. No client source PDF or client reference screenshots are included.

## Development dependencies

Playwright, PyYAML, and pypdf are installed as development/runtime dependencies rather than vendored in the skill release. Their respective upstream licenses continue to apply. Poppler and Chromium are external runtime tools and are not bundled in the release ZIP.
