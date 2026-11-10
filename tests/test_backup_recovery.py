import base64
import json
from pathlib import Path
import sqlite3
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from backup_workspace import backup,restore,verify
from praxis.server import ControlPlane,Store
from praxis.media import ingest

def test_sqlite_and_objects_restore_with_owner_session_and_hashes(tmp_path):
    api=ControlPlane(tmp_path/'source/db.sqlite');account=api.account('/api/auth/register',{'username':'backup-owner','password':'backup-test-password'})
    item=ingest(api.store,account['user']['id'],{'filename':'owned.txt','content_base64':base64.b64encode(b'owned evidence').decode()})
    snapshot=tmp_path/'private-backup';manifest=backup(api.store.path,snapshot)
    assert manifest['objects']==[item['sha256']] and verify(snapshot)==manifest
    restore(snapshot,tmp_path/'restored');api.pool.shutdown(wait=True)
    restored=ControlPlane(tmp_path/'restored/praxis.sqlite')
    try:
        assert restored.auth('Bearer '+account['token'])==account['user']['id']
        assert restored.store.get('artifact',item['id'],account['user']['id'])['sha256']==item['sha256']
        assert (tmp_path/'restored/objects'/item['sha256']).read_bytes()==b'owned evidence'
    finally:restored.pool.shutdown(wait=True)
    with pytest.raises(ValueError):restore(snapshot,tmp_path/'restored')
    with pytest.raises(ValueError):backup(tmp_path/'source/db.sqlite',snapshot)
    (snapshot/'objects'/item['sha256']).write_bytes(b'corruption')
    with pytest.raises(ValueError):verify(snapshot)
    with pytest.raises(ValueError):restore(snapshot,tmp_path/'must-not-create')
    assert not (tmp_path/'must-not-create').exists()

def test_future_schema_refused_without_modifying_existing_database(tmp_path):
    db=tmp_path/'future.sqlite'
    with sqlite3.connect(db) as c:c.execute('PRAGMA user_version=1')
    with pytest.raises(ValueError):Store(db)
    with sqlite3.connect(db) as c:assert c.execute('PRAGMA user_version').fetchone()[0]==1

def test_private_database_and_uploaded_object_permissions(tmp_path):
    import stat
    api=ControlPlane(tmp_path/'private/db.sqlite')
    try:
        account=api.account('/api/auth/register',{'username':'permissions-owner','password':'test-password-123'})
        item=ingest(api.store,account['user']['id'],{'filename':'owned.txt','content_base64':base64.b64encode(b'evidence').decode()})
        assert stat.S_IMODE((tmp_path/'private').stat().st_mode)==0o700
        assert stat.S_IMODE(Path(api.store.path).stat().st_mode)==0o600
        assert stat.S_IMODE((tmp_path/'private/objects'/item['sha256']).stat().st_mode)==0o600
    finally:api.pool.shutdown(wait=True)
