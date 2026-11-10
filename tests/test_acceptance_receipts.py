import json
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from acceptance_receipts import accepted_receipt

@pytest.mark.parametrize('value',[None,[],{}, {'status':'passed','checks':[{'passed':True}]}, {'status':'passed','source_commit':'old','source_dirty':False,'checks':[{'passed':True}]}, {'status':'passed','source_commit':'current','source_dirty':True,'checks':[{'passed':True}]}, {'status':'passed','source_commit':'current','source_dirty':False,'checks':[{'passed':False}]}])
def test_missing_stale_or_failed_receipt_cannot_count_as_acceptance(tmp_path,value):
 p=tmp_path/'receipt.json'
 if value is not None:p.write_text(json.dumps(value))
 assert accepted_receipt(p,'current')[0] is False

def test_current_checks_required_and_validated(tmp_path):
 p=tmp_path/'receipt.json';p.write_text(json.dumps({'status':'passed','source_commit':'current','source_dirty':False,'checks':[{'passed':True}]}))
 assert accepted_receipt(p,'current')[0] is True
 assert accepted_receipt(p,'current',2)[0] is False
 p.write_text('not JSON');assert accepted_receipt(p,'current')[0] is False
