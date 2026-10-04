"""Check Android URL policy against the same catalog/cases as desktop."""
import json
from pathlib import Path
import subprocess

if __package__:
    from .java_support import java_tools
else:
    from java_support import java_tools

ROOT = Path(__file__).resolve().parents[1]

def main():
    javac, java = java_tools("JDK required: set JAVA_HOME.")
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
