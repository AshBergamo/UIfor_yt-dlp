"""Locate the matching Java compiler/runtime for local Android checks."""
import os
from pathlib import Path
import shutil


def java_tools(missing_message):
    suffix = ".exe" if os.name == "nt" else ""
    java_home = os.environ.get("JAVA_HOME")
    javac = str(Path(java_home) / "bin" / ("javac" + suffix)) if java_home else shutil.which("javac")
    if not javac or not Path(javac).is_file():
        raise SystemExit(missing_message)
    java = Path(javac).resolve().with_name("java" + suffix)
    return javac, java
