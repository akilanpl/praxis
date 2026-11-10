import importlib.util
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


measure = load("diff_coverage", "scripts/diff_coverage.py").measure_diff
scorer = load("gate_score", ".pushgate/score.py")


def test_changed_executable_lines_and_missing_evidence(tmp_path):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path, text=True).strip()

    git("init", "-q")
    git("config", "user.name", "Coverage Test")
    git("config", "user.email", "coverage@example.test")
    path = tmp_path / "runner/praxis/example.py"
    path.parent.mkdir(parents=True)
    path.write_text("x = 0\n")
    git("add", ".")
    git("commit", "-qm", "baseline")
    base = git("rev-parse", "HEAD")
    path.write_text("x = 0\n# not executable\ny = 1\nz = 2\n")
    git("commit", "-qam", "change")
    evidence = {"runner/praxis/example.py": {"executed_lines": [1, 3], "missing_lines": [4]}}
    assert measure(tmp_path, base, evidence) == (50.0, "1/2 changed executable runtime lines")
    assert measure(tmp_path, base, {})[0] is None
    assert measure(tmp_path, "0" * 40, evidence)[0] is None
    assert measure(tmp_path, git("rev-parse", "HEAD"), evidence)[0] is None
    frontend = tmp_path / "apps/web/src/runtime.ts"
    frontend.parent.mkdir(parents=True)
    frontend.write_text("export const value = 1;\n")
    git("add", ".")
    git("commit", "-qm", "unmeasured runtime")
    assert measure(tmp_path, base, evidence)[0] is None


def test_unknown_diff_keeps_existing_protected_branch_cap():
    groups = scorer.CONFIG["weights"]
    tests = [{"family": family, "sev": "P1", "status": "pass"} for family in groups]
    report = {
        "branch": "main",
        "tests": tests * scorer.CONFIG["min_tests"],
        "coverage": {"line": 95, "diff": None},
        "baseline_score": 0,
        "security_clear": True,
        "environment_started": True,
    }
    result = scorer.score(report)
    assert result["score"] == 89
    assert result["decision"] == "FAIL"
    report["coverage"]["diff"] = 90
    assert scorer.score(report)["decision"] == "PASS"


def test_typescript_and_website_executable_lines_are_measured(tmp_path):
    def git(*args):return subprocess.check_output(['git',*args],cwd=tmp_path,text=True).strip()
    git('init','-q');git('config','user.name','Coverage Test');git('config','user.email','coverage@example.test')
    p=tmp_path/'apps/website/src/main.tsx';p.parent.mkdir(parents=True);p.write_text('export const initial = 0;\n');git('add','.');git('commit','-qm','base');base=git('rev-parse','HEAD')
    p.write_text('export const initial = 0;\nexport const covered = 1;\nexport const missing = 2;\n');git('commit','-qam','changed executable lines')
    evidence={'apps/website/src/main.tsx':{'statementMap':{'0':{'start':{'line':1}},'1':{'start':{'line':2}},'2':{'start':{'line':3}}},'s':{'0':1,'1':1,'2':0}}}
    assert measure(tmp_path,base,evidence)==(50.0,'1/2 changed executable runtime lines')
    evidence['apps/website/src/main.tsx']['s']['2']=1
    assert measure(tmp_path,base,evidence)==(100.0,'2/2 changed executable runtime lines')
