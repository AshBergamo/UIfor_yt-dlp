"""Shared desktop source policy and optional, media-free metadata extraction."""
import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


def catalog_path():
    base = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).parent
    return base / "resources" / "sources.json"


SOURCES = json.loads(catalog_path().read_text(encoding="utf-8"))["sources"]
EXTRACTORS = [name for source in SOURCES for name in source["extractors"]]
SOURCE_HELP = " · ".join(source["name"] + (" (experimental)" if source["experimental"] else "")
                         for source in sorted(SOURCES, key=lambda source: source["experimental"]))


def normalize_url(value):
    value = value.strip()
    return "https://" + value if value and "://" not in value else value


def classify_url(value):
    try:
        url = normalize_url(value)
        parsed = urlparse(url)
        if any(character.isspace() for character in url):
            return None
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                or parsed.username is not None or parsed.password is not None
                or parsed.port not in {None, 80, 443}):
            return None
        host = parsed.hostname.lower().rstrip(".")
        for source in SOURCES:
            for rule in source["rules"]:
                if any(host == domain or (rule.get("subdomains") and host.endswith("." + domain))
                       for domain in rule["hosts"]):
                    if re.fullmatch(rule["path"], parsed.path or "/"):
                        prefix = parsed.scheme.lower() + "://" + parsed.netloc.lower()
                        url = prefix + url.split("://", 1)[1][len(parsed.netloc):]
                        return {**source, "url": url, "short": rule.get("short", False)}
    except (ValueError, AttributeError):
        pass
    return None


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def resolve_url(url, opener=None):
    """Resolve only known sharing URLs; never fetch an unlisted destination."""
    opener = opener or build_opener(NoRedirect)
    for attempt in range(6):
        source = classify_url(url)
        if not source:
            raise ValueError("Use um link de vídeo de uma das fontes aceitas.")
        if not source["short"]:
            return source["url"]
        if attempt == 5:
            break
        request = Request(url, headers={"User-Agent": "Mozilla/5.0", "Range": "bytes=0-0"})
        try:
            with opener.open(request, timeout=5) as response:
                location = response.headers.get("Location")
        except HTTPError as error:
            try:
                location = error.headers.get("Location") if error.code in {301, 302, 303, 307, 308} else None
            finally:
                error.close()
        if not location:
            raise ValueError("Não foi possível resolver o link compartilhado. Cole o endereço da página do vídeo.")
        url = urljoin(url, location)
    raise ValueError("O link compartilhado tem redirecionamentos demais. Cole o endereço do vídeo.")


def media_filter(info, *, incomplete=False):
    if info.get("is_live") or info.get("live_status") in {"is_live", "is_upcoming"}:
        return "Transmissões ao vivo não são aceitas nesta expansão. Use um vídeo gravado ou clip."
    return None


def project_metadata(info, url):
    source = classify_url(url)
    if not source:
        raise ValueError("Fonte não aceita.")
    entries = info.get("entries") if info.get("_type") in {"playlist", "multi_video"} else None
    videos = []
    for ordinal, item in enumerate(entries if entries is not None else [info], 1):
        if not item:
            continue
        problem = media_filter(item)
        if problem:
            raise ValueError(problem)
        if item.get("vcodec") == "none" and not any(f.get("vcodec") != "none" for f in item.get("formats", [])):
            continue
        videos.append({"index": item.get("playlist_index") or ordinal,
                       "id": str(item.get("id") or ordinal),
                       "title": str(item.get("title") or f"Vídeo {ordinal}")[:300],
                       "thumbnail": item.get("thumbnail") or "",
                       "duration": item.get("duration")})
    if not videos:
        raise ValueError("Nenhum vídeo disponível nesse post.")
    return {"source": source["id"], "url": url, "videos": videos}


class SilentLogger:
    def debug(self, *_): pass
    def warning(self, *_): pass
    def error(self, *_): pass


def lookup_metadata(url, options=None):
    from yt_dlp import YoutubeDL
    url = resolve_url(url)
    opts = dict(options or {})
    # Previews never consult personal cookie files or write media/sidecars/cache.
    opts.pop("cookiefile", None)
    opts.update(quiet=True, no_warnings=True, logger=SilentLogger(), cachedir=False,
                skip_download=True, simulate=True, noplaylist=True,
                socket_timeout=5, retries=0, extractor_retries=0,
                allowed_extractors=EXTRACTORS, match_filter=media_filter)
    with YoutubeDL(opts) as downloader:
        info = downloader.extract_info(url, download=False)
    if not info:
        raise ValueError("Nenhum vídeo disponível nesse link.")
    return project_metadata(info, url)


def selection_options(metadata, selected=None):
    """Use extractor indices, including gaps, rather than visible list positions."""
    videos = metadata["videos"]
    indices = [int(item["index"]) for item in videos]
    if selected is not None and int(selected) not in indices:
        raise ValueError("Esse vídeo não está mais disponível no post. Cole o link novamente.")
    chosen = indices if selected is None else [int(selected)]
    return {"playlist_items": ",".join(map(str, chosen)), "noplaylist": True}


def friendly_error(error, source_name="Esta fonte"):
    text = re.sub(r"\x1b\[[0-9;]*m", "", str(error)).strip()
    low = text.lower()
    if any(word in low for word in ["login required", "log in", "sign in", "cookies", "private video"]):
        message = f"{source_name} exige uma sessão ou o conteúdo é restrito. Tente um vídeo público acessível sem login."
    elif any(word in low for word in ["geo", "your country", "your region"]):
        message = "Esse conteúdo não está disponível nesta região."
    elif any(word in low for word in ["429", "rate limit", "too many requests"]):
        message = "A fonte limitou as consultas. Aguarde um pouco e tente novamente."
    elif "requested format" in low:
        message = "Esse vídeo não oferece mídia compatível com o formato escolhido. Para extrair áudio, o vídeo precisa ter áudio."
    elif "audio codec" in low or "no audio" in low:
        message = "Esse vídeo não possui uma faixa de áudio que possa ser extraída para MP3/WAV."
    elif any(word in low for word in ["removed", "not available", "unavailable", "not found"]):
        message = "O vídeo foi removido, está restrito ou não está disponível."
    else:
        message = f"Não foi possível obter a mídia de {source_name}. O link ou o extrator pode precisar de atualização."
    # Keep a short diagnostic, never signed media links/cookie values.
    detail = re.sub(r"https?://\S+", "[endereço omitido]", text)[:500]
    return message + "\n\nDetalhe: " + detail
