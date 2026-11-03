"""Deterministic scorer. Missing groups and skipped checks always score zero."""
import json
from pathlib import Path
import sys
CONFIG=json.loads((Path(__file__).parent/'config.yml').read_text())
SEV={'P0':3,'P1':2,'P2':1}
VAL={'pass':1.,'flaky':.5,'fail':0.,'skip':0.,'notrun':0.}
def score(report):
    tests=report['tests'];groups={};raw=0
    for group,weight in CONFIG['weights'].items():
        rows=[t for t in tests if t['family'].startswith(group)]
        den=sum(SEV[t['sev']] for t in rows)
        rate=sum(SEV[t['sev']]*VAL[t['status']] for t in rows)/den if den else 0
        groups[group]={'weight':weight,'tests':len(rows),'passed':sum(t['status']=='pass' for t in rows),'rate':rate}
        raw+=weight*rate
    value=raw
    if any(t['sev']=='P0' and t['status']!='pass' for t in tests):value=min(value,69)
    if sum(t['status']=='flaky' for t in tests)/max(1,len(tests))>.02:value=min(value,89)
    cov=report.get('coverage',{})
    if cov.get('line',0)<80 or cov.get('diff',0)<90:value=min(value,89)
    threshold=CONFIG['thresholds']['protected'] if report.get('branch') in ('main','master') or report.get('branch','').startswith(('release/','hotfix/')) else CONFIG['thresholds']['feature']
    executed=sum(t['status'] in ('pass','fail','flaky') for t in tests)
    incomplete=(not report.get('environment_started') or any(not g['tests'] for g in groups.values()) or any(t['status'] in ('skip','notrun') for t in tests) or executed<CONFIG['min_tests'])
    baseline=report.get('baseline_score')
    ratchet_ok=baseline is not None and value>=baseline-CONFIG['thresholds']['ratchet_drop']
    passed=(not incomplete and value>=threshold and ratchet_ok and report.get('security_clear') and not any(t['sev']=='P0' and t['status']!='pass' for t in tests))
    return {'score':round(value,1),'raw_score':round(raw,1),'grade':'A' if value>=95 else 'B' if value>=90 else 'C' if value>=80 else 'D' if value>=70 else 'F','decision':'INCOMPLETE' if incomplete or not ratchet_ok else 'PASS' if passed else 'FAIL','groups':groups,'executed':executed,'threshold':threshold,'ratchet_ok':ratchet_ok,'scope':CONFIG['scope']}
if __name__=='__main__':
    path=Path(sys.argv[1]);report=json.loads(path.read_text());result=score(report);report['result']=result;path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if result['decision']=='PASS' else 1)
