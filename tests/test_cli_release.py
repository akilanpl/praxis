"""CLI acceptance against actual versioned suites and local filesystem evidence."""
import json
from pathlib import Path
import pytest
from praxis.cli import main
from praxis.engine import list_suites

@pytest.fixture
def suite_file(tmp_path):
    path=tmp_path/'suite.json'
    path.write_text(json.dumps(next(s for s in list_suites() if s['slug']=='structured-agent')))
    return path

def test_cli_lists_real_versioned_suites(capsys):
    assert main(['suites','list'])==0
    data=json.loads(capsys.readouterr().out)
    assert len(data)==6 and sum(s['task_count'] for s in data)==40

def test_cli_validation_reports_unsafe_dsl_without_execution(suite_file,capsys):
    data=json.loads(suite_file.read_text());data['tasks'][0]['assertions'][0]['op']='exec'
    suite_file.write_text(json.dumps(data))
    assert main(['validate',str(suite_file)])==1
    assert json.loads(capsys.readouterr().out)['valid'] is False

def test_cli_validate_valid_versioned_suite(suite_file,capsys):
    assert main(['validate',str(suite_file)])==0
    assert json.loads(capsys.readouterr().out)['valid'] is True

@pytest.mark.parametrize('provider,expected_status,passed',[('demo',0,8),('demo-failing',1,0)])
def test_cli_run_writes_real_fixture_assertions(tmp_path,suite_file,provider,expected_status,passed):
    output=tmp_path/'nested'/'run.json'
    assert main(['run','--suite',str(suite_file),'--provider',provider,'--output',str(output)])==expected_status
    run=json.loads(output.read_text())
    assert run['summary']['passed']==passed and run['summary']['total']==8
    assert run['trust']=='demo' and len(run['tasks'])==8
    report=tmp_path/'report.html'
    assert main(['report',str(output),'--output',str(report)])==0
    assert 'Praxis evaluation report' in report.read_text() and run['evidence_hash'] in report.read_text()

def test_cli_unknown_suite_is_useful_failure(capsys):
    assert main(['run','--suite','never-exists'])==2
    assert 'Unknown suite' in json.loads(capsys.readouterr().err)['error']

def test_cli_missing_input_file_fails_closed(tmp_path,capsys):
    assert main(['validate',str(tmp_path/'absent.json')])==2
    assert json.loads(capsys.readouterr().err)['status']=='failed'

def test_cli_world_exact_seed_replays(tmp_path):
    first=tmp_path/'first.json';second=tmp_path/'second.json'
    assert main(['world','--seed','73','--output',str(first)])==0
    assert main(['world','--seed','73','--output',str(second)])==0
    assert json.loads(first.read_text())==json.loads(second.read_text())
    assert [l['entities'] for l in json.loads(first.read_text())['levels']]==[1,5,12]

def test_cli_diagnose_labels_fixture(capsys):
    assert main(['diagnose','--provider','demo'])==0
    output=json.loads(capsys.readouterr().out)
    assert output['ok'] and output['demo']

def test_cli_diagnose_invalid_endpoint_cannot_call_provider(capsys):
    assert main(['diagnose','--provider','custom','--endpoint','file:///etc/passwd','--model','real'])==1
    output=json.loads(capsys.readouterr().out)
    assert not output['ok'] and output['category']=='invalid_endpoint'
