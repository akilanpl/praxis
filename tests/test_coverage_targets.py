import json
import subprocess
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import coverage_acceptance as coverage

def test_actual_changed_line_mapping_passes_and_missing_or_uncovered_fails(tmp_path):
    def git(*args):return subprocess.check_output(['git',*args],cwd=tmp_path,text=True).strip()
    git('init','-q');git('config','user.name','Coverage Test');git('config','user.email','coverage@example.test')
    source=tmp_path/'apps/web/src/api.ts';source.parent.mkdir(parents=True);source.write_text('export const old = 1;\n');git('add','.');git('commit','-qm','base');base=git('rev-parse','HEAD')
    source.write_text('export const old = 1;\nexport const current = 2;\n');git('commit','-qam','new code')
    py=tmp_path/'python.json';py.write_text(json.dumps({'totals':{'covered_lines':95,'num_statements':100,'covered_branches':90,'num_branches':100}}))
    entry={'statementMap':{'1':{'start':{'line':2}}},'s':{'1':1},'branchMap':{'1':{'loc':{'start':{'line':2},'end':{'line':2}}}},'b':{'1':[1,1]}}
    ts=tmp_path/'ts.json';ts.write_text(json.dumps({str(source):entry}))
    with patch.object(coverage,'ROOT',tmp_path):
        assert coverage.assess(py,ts,base)['status']=='PASS'
        entry['b']['1']=[1,0];ts.write_text(json.dumps({str(source):entry}));assert coverage.assess(py,ts,base)['status']=='FAIL'
        ts.write_text('{}');r=coverage.assess(py,ts,base);assert r['status']=='FAIL' and r['typescript']['missing_source_files']
