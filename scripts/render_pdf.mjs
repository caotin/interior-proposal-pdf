#!/usr/bin/env node
// Static paginated HTML -> PDF. Requires Playwright and a Chromium installation.
import fs from 'node:fs/promises';
import path from 'node:path';
import http from 'node:http';
import { createRequire } from 'node:module';

const usage = 'node render_pdf.mjs --html proposal.html --pdf proposal.pdf [--node-modules DIR] [--executable CHROME] [--screenshots DIR] [--report FILE]';
const args = {};
const accepted = new Set(['html', 'pdf', 'node-modules', 'executable', 'screenshots', 'report']);
for (let i = 2; i < process.argv.length; i++) {
  const key = process.argv[i].replace(/^--/, '');
  if (process.argv[i] === '--help') { console.log(usage); process.exit(0); }
  if (!accepted.has(key) || !process.argv[i + 1] || process.argv[i + 1].startsWith('--')) {
    console.error(usage); process.exit(2);
  }
  args[key] = process.argv[++i];
}
if (!args.html || !args.pdf) { console.error(usage); process.exit(2); }

const input = path.resolve(args.html);
const output = path.resolve(args.pdf);
const root = path.dirname(input);
const reportFile = path.resolve(args.report || `${output}.qa.json`);
const report = { ok: false, html: input, pdf: output, errors: [], requests: [], console_errors: [], screenshots: [] };
let server, browser;

async function loadPlaywright() {
  const roots = [args['node-modules'], ...(process.env.NODE_PATH || '').split(path.delimiter)].filter(Boolean);
  for (const dir of roots) {
    try {
      const req = createRequire(path.join(path.resolve(dir), '__skill_loader.cjs'));
      return req(path.join(path.resolve(dir), 'playwright'));
    } catch (error) {
      if (error.code !== 'MODULE_NOT_FOUND') throw error;
    }
  }
  try { return await import('playwright'); }
  catch { throw new Error('Playwright unavailable. Pass --node-modules or set NODE_PATH to a directory containing playwright.'); }
}

try {
  await fs.access(input);
  if (input === output || reportFile === input || reportFile === output) throw new Error('Input, PDF and report paths must be different');
  const playwright = await loadPlaywright();
  const rootReal = await fs.realpath(root);
  const mime = { '.html':'text/html; charset=utf-8', '.css':'text/css; charset=utf-8', '.png':'image/png', '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.webp':'image/webp', '.svg':'image/svg+xml', '.woff2':'font/woff2', '.woff':'font/woff', '.ttf':'font/ttf', '.otf':'font/otf' };
  server = http.createServer(async (req, res) => {
    try {
      const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
      const target = path.resolve(root, `.${pathname}`);
      if (target !== root && !target.startsWith(root + path.sep)) { res.writeHead(403).end(); return; }
      const real = await fs.realpath(target);
      if (real !== rootReal && !real.startsWith(rootReal + path.sep)) { res.writeHead(403).end(); return; }
      const body = await fs.readFile(real);
      res.writeHead(200, {'Content-Type':mime[path.extname(real).toLowerCase()] || 'application/octet-stream'});
      res.end(body);
    } catch { res.writeHead(404).end(); }
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  const origin = `http://127.0.0.1:${server.address().port}`;
  const executablePath = args.executable || process.env.PDF_CHROME_PATH;
  browser = await playwright.chromium.launch({ headless:true, ...(executablePath ? {executablePath} : {}) });
  const page = await browser.newPage({ viewport:{width:1280,height:720}, deviceScaleFactor:1 });
  await page.route('**/*', async route => {
    const url = route.request().url();
    if (url.startsWith(origin + '/') || url.startsWith('data:') || url.startsWith('blob:')) return route.continue();
    report.requests.push({url, status:'blocked-external'});
    await route.abort();
  });
  page.on('pageerror', error => report.console_errors.push(error.message));
  page.on('console', msg => { if (msg.type() === 'error') report.console_errors.push(msg.text()); });
  page.on('requestfailed', req => report.requests.push({url:req.url(), status:req.failure()?.errorText || 'failed'}));
  page.on('response', res => { if (res.status() >= 400) report.requests.push({url:res.url(), status:res.status()}); });
  await page.emulateMedia({media:'print'});
  await page.goto(`${origin}/${encodeURIComponent(path.basename(input))}`, {waitUntil:'networkidle', timeout:60000});
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(async img => {
      if (!img.complete) await new Promise(resolve => {img.addEventListener('load', resolve, {once:true}); img.addEventListener('error', resolve, {once:true});});
      if (img.naturalWidth > 0) await img.decode().catch(() => {});
    }));
  });
  const layout = await page.evaluate(() => {
    const errors = [], pages = [...document.querySelectorAll('.page')], seen = new Set();
    const close = (a,b) => Math.abs(a-b) < 1.1;
    const inside = (r,b) => r.left >= b.left-1.1 && r.right <= b.right+1.1 && r.top >= b.top-1.1 && r.bottom <= b.bottom+1.1;
    if (!pages.length) errors.push('No .page elements');
    const dimensions = pages.map((p, i) => {
      const id = p.dataset.pageId, b = p.getBoundingClientRect();
      if (!id || seen.has(id)) errors.push(`Page ${i+1}: missing or duplicate data-page-id`);
      seen.add(id);
      if (i && (!close(b.width,pages[0].getBoundingClientRect().width) || !close(b.height,pages[0].getBoundingClientRect().height))) errors.push(`${id}: inconsistent page size`);
      if (i && !close(b.top, pages[i-1].getBoundingClientRect().bottom)) errors.push(`${id}: print margins/gaps between pages`);
      if (p.scrollWidth > p.clientWidth+1 || p.scrollHeight > p.clientHeight+1) errors.push(`${id}: page has overflowing content`);
      for (const el of p.querySelectorAll('*')) {
        const s = getComputedStyle(el);
        if (s.display === 'none' || s.visibility === 'hidden') continue;
        if ((el.scrollWidth > el.clientWidth+1 || el.scrollHeight > el.clientHeight+1) && ['hidden','clip','auto','scroll'].some(v=>s.overflowX===v || s.overflowY===v) && el.textContent.trim()) errors.push(`${id}: clipped/scrolling text in ${el.tagName}.${el.className}`);
        for (const node of el.childNodes) {
          if (node.nodeType !== Node.TEXT_NODE || !node.textContent.trim()) continue;
          const range = document.createRange(); range.selectNodeContents(node);
          const safe = el.closest('[data-safe-area]');
          for (const r of range.getClientRects()) {
            if (!r.width || !r.height) continue;
            if (!inside(r,b)) errors.push(`${id}: text outside page: ${node.textContent.trim().slice(0,70)}`);
            if (safe && !inside(r,safe.getBoundingClientRect())) errors.push(`${id}: text outside safe area: ${node.textContent.trim().slice(0,70)}`);
          }
        }
      }
      return {id, width_px:b.width, height_px:b.height, expected_pdf_width_pt:b.width*.75, expected_pdf_height_pt:b.height*.75};
    });
    const images = [...document.images].map(img=>({src:img.getAttribute('src'), width:img.naturalWidth, height:img.naturalHeight, ok:img.complete && img.naturalWidth>0}));
    for (const img of images) if (!img.ok) errors.push(`Broken image: ${img.src}`);
    const failedFonts = [...document.fonts].filter(font=>font.status==='error').map(font=>font.family);
    if (failedFonts.length) errors.push(`Failed fonts: ${failedFonts.join(', ')}`);
    return {errors:[...new Set(errors)], page_count:pages.length, pages:dimensions, images};
  });
  Object.assign(report, layout);
  if (report.requests.length) report.errors.push('External or failed resource requests; inspect requests');
  if (report.console_errors.length) report.errors.push('Browser errors; inspect console_errors');
  if (report.errors.length) throw new Error('Preflight failed; PDF was not written. See QA report.');
  if (args.screenshots) {
    const dir = path.resolve(args.screenshots); await fs.mkdir(dir, {recursive:true});
    for (let i=0; i<layout.page_count; i++) {
      const file = path.join(dir, `page-${String(i+1).padStart(3,'0')}.png`);
      await page.locator('.page').nth(i).screenshot({path:file}); report.screenshots.push(file);
    }
  }
  await fs.mkdir(path.dirname(output), {recursive:true});
  await page.pdf({path:output, printBackground:true, preferCSSPageSize:true, displayHeaderFooter:false, margin:{top:0,right:0,bottom:0,left:0}, tagged:true});
  report.ok = true;
  console.log(JSON.stringify({ok:true, pdf:output, page_count:report.page_count, report:reportFile}));
} catch (error) {
  report.errors.push(error.message); process.exitCode = 1; console.error(error.message);
} finally {
  if (browser) await browser.close();
  if (server) await new Promise(resolve => server.close(resolve));
  await fs.mkdir(path.dirname(reportFile), {recursive:true});
  await fs.writeFile(reportFile, JSON.stringify(report,null,2)+'\n');
}
