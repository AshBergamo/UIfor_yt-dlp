# UIfor_yt-dlp · v3

[Português](README.md) · [Build and distribution](docs/BUILD.md) · [Validation](docs/VALIDATION.md)

A graphical interface for downloading and converting media without using a terminal. **yt-dlp** extracts and downloads media; **FFmpeg** converts it. This application is independent and does not modify either dependency's source code.

**The current v3 interface accepts YouTube URLs.** The redesigned UI is implemented; support for other websites is the next stage.

## How AI is used

The project started without AI and was previously closed source. AI initially began producing its evolution as an experiment to test model capabilities, mainly OpenAI models. It subsequently became the primary way of developing and maintaining this application. The UI and download integrations are produced largely autonomously, with human direction and little direct human code editing. The first publicly available version is **v3**.

This statement covers this application's code. It does not attribute AI use to yt-dlp, FFmpeg, or other dependencies unless their authors explicitly state it. No AI model runs the downloads or conversions. AI production does not imply that every line has been manually reviewed; actual checks and their limitations are recorded in [Validation](docs/VALIDATION.md).

## Current features

![Thumbnail background, dark theme — actual Windows capture](docs/images/ui-fundo-escuro.png)

![Thumbnail background, light theme — actual Windows capture](docs/images/ui-fundo-claro.png)

**Light / Dark** themes switch in place and persist between launches, preserving form fields, thumbnails and active work. The status panel displays the original media title and thumbnail when available. A failed thumbnail request keeps the generic placeholder and does not interrupt the download.

The loaded thumbnail also fills the background with a centered proportional crop, soft blur and a blue overlay in dark mode or a pearl overlay in light mode. Panels become translucent while fields, buttons and the small thumbnail stay sharp. The image fades in over 250 ms, stays fixed while scrolling and adapts to the window size. Editing/clearing the URL immediately clears the artwork. Missing thumbnails or failed effects silently retain the gradient and opaque panels. This reuses the existing image request and does not change downloaded files.

MP4/MKV select the best available video and audio and merge/remux them; source codecs vary. MP3 extraction uses a configured 192 kb/s quality. WAV extracts audio. WEBM prefers WEBM streams. GIF supports a segment up to 30 seconds, 15 fps and maximum width of 720 pixels, without audio. Playlist selection and progress reporting are included.

Windows and Linux use separate PySide6 apps with resizable native windows. The first launch is normally maximized, preserving the taskbar/system panels. Subsequent launches restore the previous geometry and maximized state. Narrow windows stack the panels and allow vertical scrolling. There is no immersive full-screen mode.

Android uses the same visual direction, a single column, visible format choices and persistent themes. MediaStore output remains `Downloads/BaixarMusicaYouTube`; the result button opens the last saved file when a compatible app is available. Application identity, signing and existing paths are preserved. The screenshots above show desktop; the APK still needs device validation. Changes do not propagate automatically between platforms.

New MP4/MKV downloads embed the original thumbnail inside the file without re-encoding video/audio or leaving a separate image. Thumbnails are converted to JPEG when needed. Videos still download if no image is available. WEBM and GIF retain their normal preview; embedded artwork display depends on the file manager/player and its cache. Previously downloaded files are not updated automatically. Artwork uses the [official yt-dlp postprocessors](https://github.com/yt-dlp/yt-dlp/blob/2026.08.19/yt_dlp/postprocessor/embedthumbnail.py).

Pasting or typing a complete video URL automatically looks up its title and original thumbnail after a 450 ms pause, before any download. This public lookup uses YouTube oEmbed without API keys or personal cookies. A failed preview stays silent and does not disable downloads; the download backend still obtains its own metadata. Changing or clearing the link discards obsolete responses. Preview supports `watch`, `youtu.be`, Shorts, live and embed links. Playlist-only URLs and private/restricted videos may have no preview.

## Run on Windows

Use 64-bit Python 3.11, then run from the repository root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/setup_tools.py --output-dir baixarMusicaYouTube/bin
.\.venv\Scripts\python.exe baixarMusicaYouTube/baixar_musica_qt.py
```

The bootstrap downloads FFmpeg/FFprobe and Deno into an ignored local directory, checks SHA256 and records versions and licenses in `bin/licenses/`. It does not install globally. Runtime lookup prefers `bin/`, then the application directory, then PATH. Packaging additionally requires tool license files.

## Run on Linux

Install Python 3.11 or newer with venv support and FFmpeg/FFprobe from your distribution. PySide6 wheels must support your platform. For Ubuntu/Debian:

```bash
sudo apt install python3 python3-venv python3-pip ffmpeg
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/setup_tools.py --system-ffmpeg --output-dir baixarMusicaYouTubeLinux/bin
.venv/bin/python baixarMusicaYouTubeLinux/baixar_musica_qt.py
```

The script copies system FFmpeg/FFprobe and downloads Deno. FFmpeg versions follow the distribution. Build Linux binaries on Linux. See [Build](docs/BUILD.md).

## Android

Android 10+ is required. Use JDK 17 and SDK 36 for builds. Open `baixarMusicaYouTubeAndroid/` in Android Studio or follow [Build](docs/BUILD.md). The existing backend is `youtubedl-android` 0.18.1 with native FFmpeg, Python and QuickJS. The app attempts a stable yt-dlp update and falls back to its bundled version. The fallback is not a guarantee of compatibility with current YouTube. EJS/QuickJS and device validation status are recorded separately.

## Optional cookies

Desktop apps do not read legacy cookie files automatically and use no cookies by default. Set `UIFOR_YTDLP_COOKIES` to an explicitly selected external Netscape cookie file:

```powershell
$env:UIFOR_YTDLP_COOKIES = 'C:\path\outside-repository\cookies.txt'
```

```bash
export UIFOR_YTDLP_COOKIES="$HOME/cookies.txt"
```

An invalid configured path produces a clear error. Cookies are never included in builds, installers, commits or reports. This setting does not change Android authentication.

## Contributing, status and license

Read [CONTRIBUTING](CONTRIBUTING.md), [SECURITY](SECURITY.md), [Roadmap](docs/ROADMAP.md) and [Validation](docs/VALIDATION.md). Download only media you are authorized to use. Website changes, login, region and codec restrictions can affect availability. This baseline does not introduce cancellation during conversion.

GitHub Actions checks desktop and builds Android after commits; it does not automatically publish releases. Previously copied EXE/APK files are local legacy artifacts, not verified releases of this baseline.

Application code is licensed under [GNU GPLv3](LICENSE). Dependencies retain their own authorship and licenses; see [third-party notices](THIRD_PARTY_NOTICES.md). The project originated in AI_PyTorch and is maintained here by AshBergamo using the AI production process described above.
