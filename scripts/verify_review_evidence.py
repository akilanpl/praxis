"""Verify historical receipts without promoting fixtures or hashes into attestation."""
import json
from pathlib import Path
import sys
from defusedxml import ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runner'))
from praxis.engine import digest
ROOT=Path(__file__).resolve().parents[1]
checks=[]
for filename in ('real-SmolLM2-135M-Instruct-ONNX.json','real-SmolLM2-360M-Instruct-ONNX.json'):
    result=json.loads((ROOT/'evidence/final'/filename).read_text())['result']
    if result['evidence_hash']!=digest({k:v for k,v in result.items() if k!='evidence_hash'}):raise RuntimeError('Historical result digest mismatch')
    if result['summary']['passed']!=0 or result['summary']['total']!=8:raise RuntimeError('Historical model result overstated')
    if any(t['artifact']['hash']!=digest(t['output']) for t in result['tasks']):raise RuntimeError('Historical output digest mismatch')
    checks.append({'artifact':filename,'status':'PASS','task_result':'FAIL','passed':0,'total':8,'trust':result['trust']})
receipt=json.loads((ROOT/'evidence/final/gate-receipt.json').read_text())
if receipt['result']['executed']!=186 or receipt['result']['score']!=89:raise RuntimeError('Historical gate accounting mismatch')
python=ET.parse(ROOT/'evidence/final/python.xml').getroot()
checks.append({'artifact':'historical Python JUnit','status':'PASS','tests':sum(int(s.attrib['tests']) for s in python.iter('testsuite')),'scope':'44 nested subtests separately counted by pytest output'})
result={'status':'PASS','scope':'historical record consistency only; NOT independent model authenticity or hosted identity attestation','checks':checks}
if __name__=='__main__':print(json.dumps(result,indent=2))
