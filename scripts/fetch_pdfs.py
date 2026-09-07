import json, os, re, time, requests, subprocess

UA = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
rows = json.load(open('data/raw/decisions_parsed.json'))
manifest = {}
for r in rows:
    slug = r['file'][:-5]
    pdfs = r['pdfs']
    manifest[slug] = []
    if not pdfs:
        continue
    pdfs_sorted = sorted(set(pdfs), key=lambda u: (0 if 'summary' in u.lower() else 1, len(u)))
    take = pdfs_sorted[:2]
    for i, u in enumerate(take):
        if u.startswith('/'):
            u = 'https://www.dataprotection.ie' + u
        fn = f"data/raw/pdfs/{slug}__{i}.pdf"
        if not os.path.exists(fn):
            try:
                resp = requests.get(u, headers=UA, timeout=(15, 120))
                if resp.status_code == 200 and resp.content[:4] == b'%PDF':
                    open(fn,'wb').write(resp.content)
                    print("GOT", slug, i, len(resp.content)//1024, "KB", flush=True)
                else:
                    print("BAD", resp.status_code, u[:110], flush=True); continue
            except Exception as e:
                print("ERR", slug, str(e)[:70], flush=True); continue
            time.sleep(0.2)
        manifest[slug].append((fn, u))
        txt = fn.replace('pdfs','pdftext').replace('.pdf','.txt')
        if not os.path.exists(txt):
            subprocess.run(['pdftotext','-q',fn,txt])
json.dump(manifest, open('data/raw/pdf_manifest.json','w'), indent=1)
n = sum(1 for v in manifest.values() if v)
print(f"DONE: decisions with PDFs: {n}/{len(manifest)}", flush=True)
print("no-pdf slugs:", [k for k,v in manifest.items() if not v], flush=True)
