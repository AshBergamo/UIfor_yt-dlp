"""Build-only resource collection shared by the two desktop specs."""
from importlib import metadata
import os
from pathlib import Path
import shutil
import sys

from PyInstaller.utils.hooks import collect_data_files


def isolate_windows_dll_search(project_dir):
    """Avoid collecting incompatible native DLLs from unrelated tools on PATH."""
    if sys.platform != "win32":
        return
    windows = Path(os.environ.get("SystemRoot", "C:/Windows"))
    python = Path(sys.base_prefix)
    trusted = [Path(project_dir) / "bin", Path(sys.executable).parent,
               python, python / "DLLs", windows / "System32", windows]
    os.environ["PATH"] = os.pathsep.join(str(path) for path in trusted if path.is_dir())


def build_inputs(project_dir):
    project_dir = Path(project_dir)
    repo = project_dir.parent
    binaries = []
    for name in ("ffmpeg", "ffprobe", "deno"):
        filename = name + ".exe" if sys.platform == "win32" else name
        candidates = [project_dir / "bin" / filename, project_dir / filename]
        found = next((p for p in candidates if p.is_file()), None)
        if found is None:
            system = shutil.which(name)
            found = Path(system) if system else None
        if found is None:
            raise RuntimeError(f"Build requires {name}. See docs/BUILD.md.")
        binaries.append((str(found), "bin"))

    # Explicit allowlist: local cookies are never resources, even if present.
    datas = [(str(project_dir / name), ".") for name in ("icon.ico", "pixil-frame-0.png")]
    datas += [(str(repo / "LICENSE"), "licenses"),
              (str(repo / "THIRD_PARTY_NOTICES.md"), "licenses")]
    datas += collect_data_files("yt_dlp_ejs")
    tool_licenses = project_dir / "bin" / "licenses"
    if not tool_licenses.is_dir():
        raise RuntimeError("Missing bin/licenses. Run scripts/setup_tools.py before packaging.")
    datas.append((str(tool_licenses), "licenses/tools"))
    for distribution in metadata.distributions():
        for file in distribution.files or ():
            if any(part.lower() in {"licenses", "license", "copying"} for part in file.parts) or file.name.lower().startswith(("license", "copying")):
                actual = distribution.locate_file(file)
                if actual.is_file():
                    dest = Path("licenses/python") / distribution.metadata["Name"] / file.parent
                    datas.append((str(actual), dest.as_posix()))
    # Tool locations were resolved above; only dependency discovery is isolated.
    # Qt's Windows ICU dependency must resolve to the OS copy, not Poppler/Conda.
    isolate_windows_dll_search(project_dir)
    return binaries, datas
