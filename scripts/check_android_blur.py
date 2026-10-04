"""Verify the Android CPU blur with the installed JDK, without a device/SDK."""
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    suffix = '.exe' if os.name == 'nt' else ''
    java_home = os.environ.get('JAVA_HOME')
    javac = str(Path(java_home) / 'bin' / ('javac' + suffix)) if java_home else shutil.which('javac')
    if not javac or not Path(javac).is_file():
        raise SystemExit('JDK required: set JAVA_HOME or add javac to PATH.')
    java = Path(javac).resolve().with_name('java' + suffix)
    output = ROOT / 'work' / 'android-blur-check'
    output.mkdir(parents=True, exist_ok=True)
    sources = [ROOT / 'baixarMusicaYouTubeAndroid/app/src/main/java/com/aipytorch/baixarmusicayoutube/ThumbnailBlur.java',
               ROOT / 'tests/android/ThumbnailBlurCheck.java']
    subprocess.run([javac, '-encoding', 'UTF-8', '-d', str(output), *map(str, sources)], check=True)
    subprocess.run([str(java), '-cp', str(output), 'com.aipytorch.baixarmusicayoutube.ThumbnailBlurCheck'], check=True)


if __name__ == '__main__':
    main()
