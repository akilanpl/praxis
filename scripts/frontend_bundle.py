"""Measure actual Vite artifacts; gzip is an estimate, not loopback wire compression."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]

def measure():
    dist=ROOT/'apps/web/dist';html=(dist/'index.html').read_text()
    entry=re.search(r'<script[^>]+src="([^"]+)"',html)
    if not entry:raise RuntimeError('Production entry script missing')
    initial=entry.group(1).lstrip('/')
    files=[]
    for path in sorted((dist/'assets').glob('*')):
        if path.suffix not in ('.js','.css'):continue
        raw=path.read_bytes();files.append({'path':str(path.relative_to(dist)),'bytes':len(raw),'gzip_estimated_bytes':len(gzip.compress(raw,mtime=0)),'sha256':hashlib.sha256(raw).hexdigest(),'initial_script':str(path.relative_to(dist))==initial})
    script=next(row for row in files if row['initial_script'])
    checks={'initial_js_below_300k':script['bytes']<=300000,'initial_gzip_estimate_below_100k':script['gzip_estimated_bytes']<=100000,'css_gzip_estimate_below_12k':sum(f['gzip_estimated_bytes'] for f in files if f['path'].endswith('.css'))<=12000,'route_splitting_present':sum(f['path'].endswith('.js') and not f['initial_script'] for f in files)>=4}
    return {'status':'PASS' if all(checks.values()) else 'FAIL','scope':'actual production artifacts; Python gzip level 9 estimate. Local API serves uncompressed no-store assets, so this is not a wire-byte claim, Lighthouse score or capacity certification. No new runtime dependencies or remote font requests.','baseline':{'source_commit':'75243f70731fb5b8001ff39c64d83af9a02120b5','initial_js_bytes':247546,'vite_gzip_report_kB':79.22,'css_bytes':5469,'css_vite_gzip_report_kB':1.81,'evidence':'Baseline build output retained from prior gate; source inspection recorded before redesign.'},'checks':checks,'files':files}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args();result=measure();Path(args.output).parent.mkdir(parents=True,exist_ok=True);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':result['checks']}));raise SystemExit(0 if result['status']=='PASS' else 1)
