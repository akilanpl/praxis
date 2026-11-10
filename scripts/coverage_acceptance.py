"""Fail-closed, separately reported Python and changed TypeScript acceptance."""
import argparse
import json
from pathlib import Path
import subprocess
from diff_coverage import HUNK
ROOT=Path(__file__).resolve().parents[1]

def assess(python,typescript,base):
    py=json.loads(Path(python).read_text())['totals']
    ts=json.loads(Path(typescript).read_text())
    expected={p.resolve() for folder in ('apps/web/src','apps/website/src','apps/api/src','packages/contracts/src') for p in (ROOT/folder).rglob('*') if p.suffix in ('.ts','.tsx')}
    covered={Path(name).resolve() for name in ts}
    missing=sorted(str(p.relative_to(ROOT)) for p in expected-covered)
    output={'base':base,'scope':'runner Python statements/branches; changed TypeScript executable lines and security-sensitive branches; controlled UI/Worker tests separate from real browser acceptance','python':{'statements':100*py['covered_lines']/py['num_statements'],'branches':100*py['covered_branches']/py['num_branches']},'typescript':{'missing_source_files':missing,'files':[]}}
    totals=[0,0,0,0]
    for name,entry in ts.items():
        path=Path(name).resolve().relative_to(ROOT).as_posix()
        patch=subprocess.check_output(['git','diff','--unified=0',base,'HEAD','--',path],cwd=ROOT,text=True)
        changed={n for start,count in HUNK.findall(patch) for n in range(int(start),int(start)+int(count or '1'))}
        lines={}
        for key,statement in entry['statementMap'].items():
            line=statement['start']['line'];lines[line]=max(lines.get(line,0),entry['s'][key])
        selected={line:hit for line,hit in lines.items() if line in changed}
        hits=sum(hit>0 for hit in selected.values());total=len(selected)
        branches=[]
        security=path.startswith(('apps/web/','apps/api/','packages/contracts/'))
        if security:
            for key,branch in entry['branchMap'].items():
                if any(line in changed for line in range(branch['loc']['start']['line'],branch['loc']['end']['line']+1)):
                    branches.extend(entry['b'][key])
        bhits=sum(hit>0 for hit in branches);btotal=len(branches)
        output['typescript']['files'].append({'path':path,'changed_executable_lines':total,'covered_lines':hits,'security_branch_outcomes':btotal,'covered_security_outcomes':bhits})
        totals=[a+b for a,b in zip(totals,[hits,total,bhits,btotal])]
    a,b,c,d=totals
    output['typescript'].update(changed_line_pct=100*a/b if b else None,security_branch_pct=100*c/d if d else None)
    output['status']='PASS' if not missing and output['python']['statements']>=90 and output['python']['branches']>=85 and b and d and 100*a/b>=85 and 100*c/d>=80 else 'FAIL'
    return output
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--python',required=True);parser.add_argument('--typescript',required=True);parser.add_argument('--base',required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
    result=assess(args.python,args.typescript,args.base);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if result['status']=='PASS' else 1)
