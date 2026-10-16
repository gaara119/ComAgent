import { build } from 'esbuild';
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
await mkdir(path.join(root,'dist','assets'),{recursive:true});
await build({absWorkingDir:root,entryPoints:['src/main.jsx'],bundle:true,minify:true,format:'esm',target:['chrome100','edge100','firefox100','safari15.4'],outfile:'dist/assets/app.js',define:{'process.env.NODE_ENV':'"production"'},legalComments:'eof',metafile:true,write:true});
const html='<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ComAgent · 可信问数</title><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 32 32%22%3E%3Crect width=%2232%22 height=%2232%22 rx=%227%22 fill=%22%23245fd1%22/%3E%3Ctext x=%229%22 y=%2224%22 fill=%22white%22 font-size=%2224%22%3EC%3C/text%3E%3C/svg%3E"><link rel="stylesheet" href="/assets/app.css"></head><body><div id="root"></div><script type="module" src="/assets/app.js"></script></body></html>\n';
await writeFile(path.join(root,'dist','index.html'),html,'utf8');
await mkdir(path.join(root,'LICENSES'),{recursive:true});
for(const name of ['react','react-dom','antd','esbuild']){
  const dir=path.join(root,'node_modules',name);const files=await readdir(dir);const file=files.find(value=>/^licen[cs]e(?:\.|$)/i.test(value));
  if(file)await writeFile(path.join(root,'LICENSES',name+'.txt'),await readFile(path.join(dir,file)));
}
console.log('Built dist/index.html and self-contained assets; no CDN runtime dependency.');
