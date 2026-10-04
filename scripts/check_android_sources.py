"""Check Android URL policy against the same catalog/cases as desktop."""
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def main():
    suffix = ".exe" if os.name == "nt" else ""
    java_home = os.environ.get("JAVA_HOME")
    javac = str(Path(java_home) / "bin" / ("javac" + suffix)) if java_home else shutil.which("javac")
    if not javac or not Path(javac).is_file():
        raise SystemExit("JDK required: set JAVA_HOME.")
    java = Path(javac).resolve().with_name("java" + suffix)
    output = ROOT / "work/android-source-check"
    output.mkdir(parents=True, exist_ok=True)
    catalog = json.loads((ROOT / "resources/sources.json").read_text(encoding="utf-8"))
    lines = []
    for source in catalog["sources"]:
        for rule in source["rules"]:
            lines.append("\t".join(["R", source["id"], ",".join(rule["hosts"]),
                                   str(rule.get("subdomains", False)).lower(), rule["path"], str(rule.get("short", False)).lower()]))
    for url, source, short in json.loads((ROOT / "tests/source_cases.json").read_text()):
        lines.append("\t".join(["C", url, source or "null", str(short).lower()]))
    data = output / "cases.tsv"
    data.write_text("\n".join(lines) + "\n", encoding="utf-8")
    sources = [ROOT / "baixarMusicaYouTubeAndroid/app/src/main/java/com/aipytorch/baixarmusicayoutube/SourcePolicy.java",
               ROOT / "tests/android/SourcePolicyCheck.java"]
    subprocess.run([javac, "-encoding", "UTF-8", "-d", str(output), *map(str, sources)], check=True)
    subprocess.run([str(java), "-cp", str(output), "com.aipytorch.baixarmusicayoutube.SourcePolicyCheck", str(data)], check=True)

if __name__ == "__main__":
    main()
