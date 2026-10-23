import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const style = `<style>@page{size:1280px 720px;margin:0}*{box-sizing:border-box}html,body{margin:0}.page{position:relative;width:1280px;height:720px;break-after:page}.page:last-child{break-after:auto}.safe{position:absolute;inset:48px 54px 66px}h1{font:48px Georgia}img{width:20px;height:20px}</style>`;
const base = `<!doctype html><html lang="en"><head><meta charset="utf-8">${style}</head><body><section class="page" data-page-id="one"><main class="safe" data-safe-area><h1>A quiet room</h1><p>Readable local document content.</p></main></section></body></html>`;
const cases = [
  { name:'valid local HTML exports PDF', html:base, ok:true },
  { name:'missing image blocks export', html:base.replace('<h1>', '<img src="missing.png" alt="Missing"><h1>'), error:/Broken image/ },
  { name:'text beyond the page blocks export', html:base.replace('<h1>', '<h1 style="position:absolute;left:1300px">'), error:/text outside page/ },
  { name:'duplicate page identifiers block export', html:base.replace('</body>', '<section class="page" data-page-id="one"><p>Second page</p></section></body>'), error:/duplicate data-page-id/ },
  { name:'external asset request blocks export', html:base.replace('</head>', '<link rel="stylesheet" href="https://example.com/remote.css"></head>'), error:/External or failed resource/ },
];

for (const fixture of cases) {
  await test(fixture.name, async () => {
    const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'interior-pdf-test-'));
    try {
      const html = path.join(dir, 'input.html'), pdf = path.join(dir, 'output.pdf'), reportPath = path.join(dir, 'report.json');
      await fs.writeFile(html, fixture.html);
      const cli = [path.join(root,'scripts/render_pdf.mjs'), '--html', html, '--pdf', pdf, '--report', reportPath];
      if (process.env.NODE_PATH) cli.push('--node-modules', process.env.NODE_PATH.split(path.delimiter)[0]);
      const result = spawnSync(process.execPath, cli, {encoding:'utf8', timeout:90000, env:process.env});
      assert.ifError(result.error);
      const report = JSON.parse(await fs.readFile(reportPath, 'utf8'));
      if (fixture.ok) {
        assert.equal(result.status, 0, result.stderr);
        assert.equal(report.ok, true);
        assert.equal(report.page_count, 1);
        assert.equal(report.pages[0].expected_pdf_width_pt, 960);
        assert.equal(report.pages[0].expected_pdf_height_pt, 540);
        assert.ok((await fs.stat(pdf)).size > 0);
      } else {
        assert.notEqual(result.status, 0);
        assert.equal(report.ok, false);
        assert.match(report.errors.join('\n'), fixture.error);
        await assert.rejects(fs.access(pdf));
      }
    } finally { await fs.rm(dir, {recursive:true, force:true}); }
  });
}
