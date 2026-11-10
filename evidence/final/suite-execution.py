"""Owned regression HTTP fixture, not a deployed app or model inference."""
import json
from pathlib import Path
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from praxis.engine import execute_run,list_suites,digest
from praxis.cli import report_html
OUT=Path(__file__).resolve().parent/'suite-runs';OUT.mkdir(exist_ok=True)
class Owned(BaseHTTPRequestHandler):
    failing=False
    def log_message(self,*args):pass
    def respond(self,status,body):
        data=json.dumps(body).encode();self.send_response(status);self.send_header('Content-Type','text/plain' if self.failing else 'application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_GET(self):self.respond(500 if self.failing else 200 if self.path=='/health' else 404,{'status':'wrong' if self.failing else 'ok'})
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        assert self.path=='/orders' and body=={'quantity':0}
        self.respond(500 if self.failing else 422,{} if self.failing else {'field':'quantity'})
server=ThreadingHTTPServer(('127.0.0.1',0),Owned);thread=threading.Thread(target=server.serve_forever);thread.start();rows=[]
try:
    for suite in list_suites():
        for passing in (True,False):
            kind='application' if suite['slug']=='http-application' else 'agent' if suite['slug']=='agent-workflows' else 'model'
            target={'kind':kind,'provider':'custom' if kind=='application' else 'demo' if passing else 'demo-failing','name':'Owned HTTP regression fixture' if kind=='application' else 'Explicit deterministic regression fixture'}
            if kind=='application':target.update(endpoint=f'http://127.0.0.1:{server.server_port}',authorized=True,allow_mutation=True);Owned.failing=not passing
            run=execute_run(target,suite)
            assert run['summary']['passed']==(len(suite['tasks']) if passing else 0)
            assert run['summary']['executed']==len(suite['tasks'])
            assert run['evidence_hash']==digest({k:v for k,v in run.items() if k!='evidence_hash'})
            name=suite['slug']+('-passing' if passing else '-failing')
            (OUT/(name+'.json')).write_text(json.dumps(run,indent=2)+'\n')
            (OUT/(name+'.html')).write_text(report_html(run))
            rows.append({'suite':suite['slug'],'version':suite['version'],'kind':kind,'case':'passing' if passing else 'failing','passed':run['summary']['passed'],'total':run['summary']['total'],'trust':run['trust'],'evidence_hash':run['evidence_hash']})
finally:server.shutdown();server.server_close();thread.join()
assert len(rows)==12 and sum(r['total'] for r in rows)==80
(OUT.parent/'suite-matrix.json').write_text(json.dumps({'status':'passed','scope':'all 40 public scenarios in positive and negative executions; deterministic model/tool fixtures, actual HTTP against an explicitly owned regression server; no neural inference in this receipt','runs':rows},indent=2)+'\n')
