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
