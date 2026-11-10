"""Expose bounded failure identifiers through the checks API, without raw logs."""
import json
from pathlib import Path
import re
import subprocess
from defusedxml import ElementTree as ET


def emit(message):
    # Only identifiers, counts and exit codes: never exception bodies or logs.
    safe = re.sub(r"[^a-zA-Z0-9_. /:(),=+-]", "_", message)[:1500]
    print("::error title=Verification failure identifiers::" + safe)


for path in (Path("work/ci-python.xml"), Path(".pushgate/reports/python.xml")):
    if path.exists():
        for case in ET.parse(path).iter("testcase"):
            if case.find("failure") is not None or case.find("error") is not None:
                emit(case.get("classname", "") + "." + case.get("name", ""))
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
path = Path(".pushgate/reports") / (sha + ".json")
if path.exists():
    value = json.loads(path.read_text())
    for stage in value.get("stages", []):
        if stage["exit_code"]:
            emit("stage " + stage["name"] + " exit=" + str(stage["exit_code"]))
    for test in value.get("tests", []):
        if test["status"] != "pass":
            emit(test["id"] + " " + test["name"] + " " + test["status"])
    targets = Path(".pushgate/reports/coverage-targets.json")
    if targets.exists():
        coverage = json.loads(targets.read_text())
        emit("coverage diagnostics " + json.dumps({
            "python": coverage.get("python"),
            "changed_lines": coverage.get("typescript", {}).get("changed_line_pct"),
            "security_branches": coverage.get("typescript", {}).get("security_branch_pct"),
            "missing_sources": len(coverage.get("typescript", {}).get("missing_source_files", [])),
        }))
    postgres = Path("work/acceptance") / sha / "postgres.json"
    if postgres.exists():
        database = json.loads(postgres.read_text())
        emit("disposable database checks completed=" + str(len(database.get("checks", []))))
        # This receipt comes only from our constant-fixture, disposable DB script.
        # Remove quoted SQL values and paths; never expose arbitrary test logs.
        error = re.sub(r"'[^']*'|\"[^\"]*\"|/\S+", "_", database.get("error", ""))
        if error:
            emit("disposable database failure " + error[:400])
