"""Real disposable filesystem/SQLite failures plus explicit syscall fault injection."""
import base64
import errno
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
from unittest.mock import patch
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import backup_workspace as recovery
from praxis.media import ingest
from praxis.server import ControlPlane, Store

@pytest.fixture
def workspace(tmp_path):
    app=ControlPlane(tmp_path/'source #? with spaces'/'praxis.sqlite')
    account=app.account('/api/auth/register',{'username':'recovery-owner','password':'test-password-123'})
    yield app,account['user']['id']
    app.pool.shutdown(wait=True)

def upload(app,owner):
    return ingest(app.store,owner,{'filename':'evidence.txt','content_base64':base64.b64encode(b'private evidence').decode()})

def test_uri_special_paths_backup_and_foreign_key_integrity(workspace,tmp_path):
    app,owner=workspace;upload(app,owner)
    target=tmp_path/'snapshot #? with spaces';recovery.backup(app.store.path,target)
    assert recovery.verify(target)['objects']
    with sqlite3.connect(target/'praxis.sqlite') as db:
        db.execute("INSERT INTO records VALUES('bad','artifact','missing-owner','{}',0)")
    manifest=json.loads((target/'manifest.json').read_text());manifest['database_sha256']=recovery.sha(target/'praxis.sqlite');(target/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='ownership'):recovery.verify(target)

def test_real_permission_denial_preserves_database(workspace,tmp_path):
    if os.name!='posix':pytest.fail('This release qualification requires POSIX permissions; Windows is not qualified')
    app,owner=workspace;folder=tmp_path/'denied';folder.mkdir();folder.chmod(0o500)
    before=recovery.sha(app.store.path)
    try:
        with pytest.raises(PermissionError):recovery.backup(app.store.path,folder/'snapshot')
    finally:folder.chmod(0o700)
    assert recovery.sha(app.store.path)==before and not (folder/'snapshot').exists()
    assert app.store.all('artifact',owner)==[]

def test_atomic_upload_enospc_fault_has_no_record_or_partial_object(workspace):
    app,owner=workspace
    with patch('praxis.media.os.fsync',side_effect=OSError(errno.ENOSPC,'Injected full device')):
        with pytest.raises(OSError) as error:upload(app,owner)
    assert error.value.errno==errno.ENOSPC
    assert not app.store.all('artifact',owner)
    assert list((Path(app.store.path).parent/'objects').iterdir())==[]
    item=upload(app,owner);assert item['sha256']==hashlib.sha256(b'private evidence').hexdigest()

def test_backup_copy_enospc_fault_is_not_published(workspace,tmp_path):
    app,owner=workspace;upload(app,owner);destination=tmp_path/'snapshot'
    with patch.object(recovery.shutil,'copyfile',side_effect=OSError(errno.ENOSPC,'Injected full device')):
        with pytest.raises(OSError):recovery.backup(app.store.path,destination)
    assert not destination.exists() and not list(tmp_path.glob('.praxis-backup-*'))
    recovery.backup(app.store.path,destination);assert recovery.verify(destination)['objects']

def test_actual_sqlite_full_rolls_back_partial_transaction(workspace):
    app,owner=workspace
    with app.store.connect() as db:
        pages=db.execute('PRAGMA page_count').fetchone()[0];db.execute('PRAGMA max_page_count='+str(pages))
        try:
            db.execute('BEGIN');db.execute("INSERT INTO audit(actor,action,created) VALUES(?,?,0)",(owner,'must rollback'))
            db.execute('INSERT INTO records VALUES(?,?,?,?,?)',('full','artifact',owner,json.dumps({'content':'x'*(1024*1024)}),0))
            pytest.fail('SQLite full condition was not exercised')
        except sqlite3.OperationalError as error:
            assert error.sqlite_errorcode==sqlite3.SQLITE_FULL
            db.rollback()
        assert db.execute("SELECT count(*) FROM records WHERE id='full'").fetchone()[0]==0
        assert db.execute("SELECT count(*) FROM audit WHERE action='must rollback'").fetchone()[0]==0
        db.execute('PRAGMA max_page_count=1073741823')
    assert upload(app,owner)['sha256']

def test_corrupt_database_and_missing_artifact_fail_without_restore(workspace,tmp_path):
    app,owner=workspace;item=upload(app,owner);snapshot=tmp_path/'snapshot';recovery.backup(app.store.path,snapshot)
    (snapshot/'objects'/item['sha256']).unlink()
    with pytest.raises(OSError):recovery.restore(snapshot,tmp_path/'restored')
    assert not (tmp_path/'restored').exists()
    bad=tmp_path/'corrupt.sqlite';bad.write_bytes(b'not sqlite')
    with pytest.raises(sqlite3.DatabaseError):Store(bad)
    assert bad.read_bytes()==b'not sqlite'

def test_backup_rejects_future_schema_and_duplicate_manifest_entries(workspace,tmp_path):
    app,owner=workspace;upload(app,owner);snapshot=tmp_path/'snapshot';recovery.backup(app.store.path,snapshot)
    m=json.loads((snapshot/'manifest.json').read_text());m['objects']*=2;(snapshot/'manifest.json').write_text(json.dumps(m))
    with pytest.raises(ValueError,match='referenced'):recovery.verify(snapshot)
    m['objects']=list(set(m['objects']))
    with sqlite3.connect(snapshot/'praxis.sqlite') as db:db.execute('PRAGMA user_version=99')
    m['database_sha256']=recovery.sha(snapshot/'praxis.sqlite');(snapshot/'manifest.json').write_text(json.dumps(m))
    with pytest.raises(ValueError,match='schema'):recovery.restore(snapshot,tmp_path/'future')
    assert not (tmp_path/'future').exists()

def test_optimized_infrastructure_proof_refuses_before_workspace_access(tmp_path):
    import subprocess
    script=Path(__file__).resolve().parents[1]/'scripts/integration_proof.py'
    result=subprocess.run([sys.executable,'-O',str(script)],cwd=tmp_path,capture_output=True,text=True,timeout=10)
    assert result.returncode!=0 and 'Verification requires Python assertions enabled' in result.stderr
    assert not list(tmp_path.iterdir())

def test_real_process_kill_marks_active_run_interrupted_and_can_run_again(tmp_path):
    import http.server
    import secrets
    import socket
    import subprocess
    import threading
    import time
    import urllib.request
    accepted=threading.Event();release=threading.Event()
    class Provider(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']));accepted.set();release.wait(15)
            try:
                self.send_response(200);self.end_headers();self.wfile.write(b'{"output":"late"}')
            except (BrokenPipeError,ConnectionResetError):pass
    provider=http.server.ThreadingHTTPServer(('127.0.0.1',0),Provider)
    thread=threading.Thread(target=provider.serve_forever);thread.start()
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    root=Path(__file__).resolve().parents[1];base='http://127.0.0.1:'+str(port);token='';process=None
    def call(method,path,body=None):
        req=urllib.request.Request(base+path,method=method,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json','Authorization':'Bearer '+token})
        with urllib.request.urlopen(req,timeout=3) as response:return json.load(response)
    def start():
        proc=subprocess.Popen([sys.executable,'-m','praxis.server'],cwd=root,env=dict(os.environ,PYTHONPATH=str(root/'runner'),PRAXIS_PORT=str(port),PRAXIS_DB=str(tmp_path/'private'/'praxis.sqlite')),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(100):
            assert proc.poll() is None
            try:
                if call('GET','/api/health')['ok']:return proc
            except OSError:time.sleep(.05)
        proc.kill();proc.wait();pytest.fail('Disposable API startup failed')
    try:
        process=start()
        account=call('POST','/api/auth/register',{'username':'interruption-owner','password':secrets.token_urlsafe(24)});token=account['token']
        target=call('POST','/api/targets',{'name':'Owned stalled model','kind':'model','model':'explicit-stall-fixture','provider':'custom','endpoint':'http://127.0.0.1:'+str(provider.server_port),'timeout':10})
        run=call('POST','/api/runs',{'target_id':target['id'],'suite_slug':'structured-agent'})
        assert accepted.wait(5),'Real provider HTTP request never executed'
        active=call('GET','/api/runs/'+run['id']);assert active['status']=='running'
        process.kill();process.wait(timeout=5);process=start()
        interrupted=call('GET','/api/runs/'+run['id'])
        assert interrupted['status']=='interrupted' and 'restarted' in interrupted['error']
        assert interrupted['events']==active['events'] and not interrupted.get('result')
        fixture=call('POST','/api/targets',{'name':'Explicit recovery fixture','kind':'model','provider':'demo'})
        retry=call('POST','/api/runs',{'target_id':fixture['id'],'suite_slug':'structured-agent'})
        for _ in range(100):
            retry=call('GET','/api/runs/'+retry['id'])
            if retry['status']=='completed':break
            time.sleep(.05)
        assert retry['result']['summary']['passed']==8 and retry['trust']=='demo'
    finally:
        release.set()
        if process is not None and process.poll() is None:process.kill();process.wait(timeout=5)
        provider.shutdown();provider.server_close();thread.join()
