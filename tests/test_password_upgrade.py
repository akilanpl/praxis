import hashlib
import pytest
from praxis.server import ControlPlane,APIError,PASSWORD_PREFIX,password_matches

def test_new_hashes_and_legacy_login_upgrade_without_reset(tmp_path):
    api=ControlPlane(tmp_path/'db')
    try:
        account=api.account('/api/auth/register',{'username':'modern-owner','password':'fixture-password-123'})
        with api.store.connect() as db:
            stored=db.execute('SELECT password FROM users WHERE id=?',(account['user']['id'],)).fetchone()[0]
            assert stored.startswith(PASSWORD_PREFIX)
            salt='synthetic-salt';legacy=hashlib.pbkdf2_hmac('sha256',b'fixture-password-123',salt.encode(),240000).hex()
            db.execute('INSERT INTO users VALUES(?,?,?,?,?)',('legacy','legacy-owner',salt,legacy,0))
        with pytest.raises(APIError):api.account('/api/auth/login',{'username':'legacy-owner','password':'incorrect-password'})
        with api.store.connect() as db:assert db.execute("SELECT password FROM users WHERE id='legacy'").fetchone()[0]==legacy
        login=api.account('/api/auth/login',{'username':'legacy-owner','password':'fixture-password-123'})
        assert api.auth('Bearer '+login['token'])=='legacy'
        with api.store.connect() as db:
            row=db.execute("SELECT salt,password FROM users WHERE id='legacy'").fetchone();assert row['salt']!=salt and row['password'].startswith(PASSWORD_PREFIX)
        assert api.account('/api/auth/login',{'username':'legacy-owner','password':'fixture-password-123'})['user']['id']=='legacy'
        assert not password_matches('fixture-password-123',salt,'unsupported$900000000$hash')
    finally:api.pool.shutdown(wait=True)

@pytest.mark.parametrize('username',[None,{},True,123])
def test_username_requires_string(tmp_path,username):
    api=ControlPlane(tmp_path/'db')
    try:
        with pytest.raises(APIError) as e:api.account('/api/auth/register',{'username':username,'password':'fixture-password-123'})
        assert e.value.status==400
    finally:api.pool.shutdown(wait=True)
