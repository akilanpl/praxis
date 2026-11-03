"""Praxis CLI, local evidence and portable print reports."""
import argparse
import html
import json
import os
import sys
import urllib.request
from pathlib import Path
from .adapters import diagnose
from .engine import execute_run, list_suites, validate_suite
from .worlds import run_world

def _save(value,path):
    text=json.dumps(value,indent=2,ensure_ascii=False)+"\n"
    if path:
        dest=Path(path)
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(text)
    else:
        print(text,end="")

def report_html(result):
    esc=lambda v:html.escape(str(v))
    rows=[]
    for task in result.get("tasks",[]):
        checks="".join('<li>%s %s</li>'%("PASS" if a['passed'] else "FAIL",esc(a['name'])) for a in task['assertions'])
        rows.append('<article><h2>%s — %s</h2><p>%s ms</p><ul>%s</ul><pre>%s</pre></article>'%(esc(task['id']),"PASS" if task['passed'] else "FAIL",esc(task['latency_ms']),checks,esc(json.dumps(task['output'],indent=2))))
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'"><title>Praxis run report</title><style>body{font:16px system-ui;margin:32px;max-width:960px;color:#18221e}article{border:1px solid #ccc;padding:16px;margin:16px 0;break-inside:avoid}pre{white-space:pre-wrap;overflow-wrap:anywhere}h1{font-size:36px}@media print{body{margin:0}}</style><h1>Praxis evaluation report</h1><p>Trust: %s · suite %s v%s · seed %s</p><p>Passed %s / %s. Cost: unknown. Self-reported and demo results are excluded from official rankings.</p><p>Evidence hash: %s</p>%s</html>'%(esc(result.get('trust')),esc(result.get('suite_slug')),esc(result.get('suite_version')),esc(result.get('seed')),esc(result.get('summary',{}).get('passed')),esc(result.get('summary',{}).get('total')),esc(result.get('evidence_hash')),"".join(rows))

def main(argv=None):
    parser=argparse.ArgumentParser(prog="praxis",description="User-controlled, artifact-first AI evaluation")
    sub=parser.add_subparsers(dest='command',required=True)
    suites=sub.add_parser('suites')
    suites.add_argument('action',choices=['list'])
    run=sub.add_parser('run')
    run.add_argument('--suite',default='structured-agent')
    run.add_argument('--provider',choices=['demo','demo-failing','openai','ollama','custom'],default='demo')
    run.add_argument('--endpoint',default='')
    run.add_argument('--model',default='')
    run.add_argument('--kind',choices=['model','agent','application'],default='model')
    run.add_argument('--key-env',default='PRAXIS_MODEL_API_KEY')
    run.add_argument('--seed',type=int,default=73)
    run.add_argument('--output',default='')
    run.add_argument('--timeout',type=float,default=20)
    run.add_argument('--max-tokens',type=int,default=1024)
    validate=sub.add_parser('validate')
    validate.add_argument('file')
    report=sub.add_parser('report')
    report.add_argument('file')
    report.add_argument('--output',required=True)
    world=sub.add_parser('world')
    world.add_argument('--domain',default='customer-support',choices=['customer-support','research','workflow','web-product'])
    world.add_argument('--seed',type=int,default=73)
    world.add_argument('--max-level',type=int,default=3)
    world.add_argument('--max-steps',type=int,default=64)
    world.add_argument('--output',default='')
    web=sub.add_parser('check-website')
    web.add_argument('--output-dir',default='data/website-proof')
    diagnose_parser=sub.add_parser('diagnose')
    diagnose_parser.add_argument('--provider',required=True,choices=['demo','openai','ollama','custom'])
    diagnose_parser.add_argument('--endpoint',default='')
    diagnose_parser.add_argument('--model',default='')
    args=parser.parse_args(argv)
    try:
        if args.command=='suites':
            _save([{k:s[k] for k in ('slug','version','title','track')} | {'task_count':len(s['tasks'])} for s in list_suites()],None)
        elif args.command=='run':
            path=Path(args.suite)
            suite=json.loads(path.read_text()) if path.is_file() else next((s for s in list_suites() if s['slug']==args.suite),None)
            if suite is None:
                raise ValueError('Unknown suite')
            result=execute_run(vars(args),suite,seed=args.seed)
            _save(result,args.output)
            return 0 if result['summary']['passed']==result['summary']['total'] else 1
        elif args.command=='validate':
            result=validate_suite(json.loads(Path(args.file).read_text()))
            _save(result,None)
            return 0 if result['valid'] else 1
        elif args.command=='report':
            Path(args.output).write_text(report_html(json.loads(Path(args.file).read_text())) )
        elif args.command=='world':
            _save(run_world({'domain':args.domain,'max_level':args.max_level,'max_steps':args.max_steps},seed=args.seed),args.output)
        elif args.command=='check-website':
            from .artifact_checks import check_owned_website
            result=check_owned_website(args.output_dir)
            _save(result,None)
            return 0 if result['passed'] else 1
        elif args.command=='diagnose':
            result=diagnose(vars(args))
            _save(result,None)
            return 0 if result['ok'] else 1
    except (OSError,ValueError,RuntimeError,ImportError) as exc:
        print(json.dumps({'error':str(exc),'status':'failed'}),file=sys.stderr)
        return 2
    return 0
