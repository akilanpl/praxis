"""Private SQLite/object snapshot and verified restore to a NEW directory only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verify(directory):
    directory=Path(directory);manifest=json.loads((directory/'manifest.json').read_text())
    objects=manifest.get('objects')
    if manifest.get('format')!='praxis.backup.v1' or not isinstance(objects,list) or any(not isinstance(x,str) or re.fullmatch('[a-f0-9]{64}',x) is None for x in objects):raise ValueError('Invalid backup manifest')
    db=directory/'praxis.sqlite'
    if db.is_symlink() or sha(db)!=manifest.get('database_sha256'):raise ValueError('Database backup integrity failed')
    with sqlite3.connect(f'file:{db}?mode=ro',uri=True) as connection:
        if connection.execute('PRAGMA quick_check').fetchone()[0]!='ok' or connection.execute('PRAGMA user_version').fetchone()[0]!=0:raise ValueError('Unsupported or corrupt database schema')
    for name in objects:
        obj=directory/'objects'/name
        if obj.is_symlink() or sha(obj)!=name:raise ValueError('Artifact backup integrity failed')
    return manifest

def backup(database,directory):
    database,directory=Path(database),Path(directory)
    if not database.is_file():raise ValueError('Source database is missing')
    if directory.exists():raise ValueError('Backup destination must not exist')
    directory.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.praxis-backup-',dir=directory.parent) as folder:
        folder=Path(folder);os.chmod(folder,0o700);snapshot=folder/'praxis.sqlite'
        with sqlite3.connect(f'file:{database}?mode=ro',uri=True) as source,sqlite3.connect(snapshot) as target:source.backup(target)
        with sqlite3.connect(snapshot) as target:
            uploaded=[json.loads(row[0]) for row in target.execute("SELECT data FROM records WHERE kind='artifact'")]
        names=sorted({r['sha256'] for r in uploaded if 'filename' in r})
        (folder/'objects').mkdir(mode=0o700)
        for name in names:
            if not isinstance(name,str) or re.fullmatch('[a-f0-9]{64}',name) is None:raise ValueError('Invalid stored object digest')
            shutil.copyfile(database.parent/'objects'/name,folder/'objects'/name);os.chmod(folder/'objects'/name,0o600)
        manifest={'format':'praxis.backup.v1','database_sha256':sha(snapshot),'objects':names}
        (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');os.chmod(snapshot,0o600);os.chmod(folder/'manifest.json',0o600)
        verify(folder);os.replace(folder,directory)
    return manifest

def restore(source,directory):
    source,directory=Path(source),Path(directory)
    manifest=verify(source)
    if directory.exists():raise ValueError('Restore destination must not exist; never overwrite an active workspace')
    directory.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.praxis-restore-',dir=directory.parent) as folder:
        folder=Path(folder);os.chmod(folder,0o700);(folder/'objects').mkdir(mode=0o700)
        for name in ('praxis.sqlite','manifest.json'):
            shutil.copyfile(source/name,folder/name);os.chmod(folder/name,0o600)
        for name in manifest['objects']:
            shutil.copyfile(source/'objects'/name,folder/'objects'/name);os.chmod(folder/'objects'/name,0o600)
        verify(folder);os.replace(folder,directory)
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['backup','verify','restore']);parser.add_argument('--directory',required=True);parser.add_argument('--database');parser.add_argument('--source');args=parser.parse_args()
    try:
        result=backup(args.database,args.directory) if args.action=='backup' else restore(args.source,args.directory) if args.action=='restore' else verify(args.directory)
        print(json.dumps({'status':'PASS','objects':len(result['objects']),'directory':args.directory}))
    except (OSError,ValueError,sqlite3.Error,TypeError,KeyError) as error:
        print(json.dumps({'status':'FAIL','error':type(error).__name__}));raise SystemExit(1)
