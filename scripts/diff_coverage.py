"""Measure changed runtime statements using coverage.py line evidence."""

import re
import subprocess
from pathlib import Path

RUNTIME_ROOTS = ("runner/praxis/", "apps/web/", "apps/api/", "packages/contracts/")
SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".svelte", ".vue"}
HUNK = re.compile(r"^@@ .* \+(\d+)(?:,(\d+))? @@", re.MULTILINE)
SHA = re.compile(r"[0-9a-f]{40}")


def measure_diff(root, base, coverage_files):
    """Return a percentage and a status. Unknown input stays unmeasured."""
    if not base or not SHA.fullmatch(base) or not isinstance(coverage_files, dict):
        return None, "missing baseline or coverage files"

    def git(*args):
        return subprocess.check_output(
            ["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL
        )

    try:
        names = git(
            "diff", "--name-only", "-z", "--no-renames", "--diff-filter=AMT", base, "HEAD"
        ).split("\0")
        files = {(root / key).resolve(): value for key, value in coverage_files.items()}
        total = covered = 0
        for name in names:
            path = Path(name)
            if not name.startswith(RUNTIME_ROOTS) or path.suffix not in SOURCE_SUFFIXES:
                continue
            if any(part in {"test", "tests", "__tests__"} for part in path.parts):
                continue
            patch = git("diff", "--no-renames", "--no-ext-diff", "--no-textconv",
                        "--unified=0", base, "HEAD", "--", name)
            hunks = HUNK.findall(patch)
            if not hunks and ("Binary files " in patch or "GIT binary patch" in patch):
                return None, f"binary runtime source: {name}"
            changed = {
                line
                for start, count in hunks
                for line in range(int(start), int(start) + int(count or "1"))
            }
            if not changed:
                continue
            evidence = files.get((root / path).resolve())
            if path.suffix != ".py" or evidence is None:
                return None, f"no executable-line coverage for {name}"
            executed = set(evidence["executed_lines"])
            missed = set(evidence["missing_lines"])
            excluded = set(evidence.get("excluded_lines", []))
            if changed & excluded:
                return None, f"changed lines excluded from coverage in {name}"
            total += len(changed & (executed | missed))
            covered += len(changed & executed)
    except (subprocess.CalledProcessError, OSError, TypeError, KeyError, ValueError):
        return None, "could not read diff or coverage evidence"
    if total == 0:
        return None, "no changed executable runtime lines"
    return 100 * covered / total, f"{covered}/{total} changed executable runtime lines"
