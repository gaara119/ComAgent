import { build } from 'esbuild';
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
await mkdir(path.join(root,'dist','assets'),{recursive:true});
await build({absWorkingDir:root,entryPoints:['src/main.jsx'],bundle:true,minify:true,format:'esm',target:['chrome100','edge100','firefox100','safari15.4'],outfile:'dist/assets/app.js',define:{'process.env.NODE_ENV':'"production"'},legalComments:'eof',metafile:true,write:true});
const html='<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><meta name="description" content="白色立体数据工作台：数据库问数、文档问答、跨源查询与结果可视化。"><title>ComAgent · 数据分析中心</title><link rel="icon" href="data:,"><link rel="stylesheet" href="/assets/app.css"></head><body><div id="root"></div><script type="module" src="/assets/app.js"></script></body></html>\n';
await writeFile(path.join(root,'dist','index.html'),html,'utf8');
await mkdir(path.join(root,'LICENSES'),{recursive:true});
for(const name of ['react','react-dom','antd','esbuild']){
  const dir=path.join(root,'node_modules',name);const files=await readdir(dir);const file=files.find(value=>/^licen[cs]e(?:\.|$)/i.test(value));
  if(file)await writeFile(path.join(root,'LICENSES',name+'.txt'),await readFile(path.join(dir,file)));
}
console.log('Built dist/index.html and self-contained assets; no CDN runtime dependency.');
