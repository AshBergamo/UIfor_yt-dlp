"""Verify the Android CPU blur with the installed JDK, without a device/SDK."""
from pathlib import Path
import subprocess

if __package__:
    from .java_support import java_tools
else:
    from java_support import java_tools

ROOT = Path(__file__).resolve().parents[1]


def main():
    javac, java = java_tools('JDK required: set JAVA_HOME or add javac to PATH.')
    output = ROOT / 'work' / 'android-blur-check'
    output.mkdir(parents=True, exist_ok=True)
    sources = [ROOT / 'baixarMusicaYouTubeAndroid/app/src/main/java/com/aipytorch/baixarmusicayoutube/ThumbnailBlur.java',
               ROOT / 'tests/android/ThumbnailBlurCheck.java']
    subprocess.run([javac, '-encoding', 'UTF-8', '-d', str(output), *map(str, sources)], check=True)
    subprocess.run([str(java), '-cp', str(output), 'com.aipytorch.baixarmusicayoutube.ThumbnailBlurCheck'], check=True)


if __name__ == '__main__':
    main()
