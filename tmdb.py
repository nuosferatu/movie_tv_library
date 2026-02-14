import json
import os
import socket
import urllib.request
import urllib.parse
from model import Media, Season, Episode

# 优先 IPv4，避免无 IPv6 路由时 Network unreachable
_orig_getaddrinfo = socket.getaddrinfo
def _getaddrinfo_ipv4_first(host, port, family=0, type=0, proto=0, flags=0):
    if family == socket.AF_UNSPEC:
        try:
            return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
        except OSError:
            pass
    return _orig_getaddrinfo(host, port, family, type, proto, flags)
socket.getaddrinfo = _getaddrinfo_ipv4_first

BASE = "https://api.themoviedb.org/3"
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

TIMEOUT = 15

_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
_opener = None


def _build_opener():
    global _opener
    if _opener is not None:
        return _opener
    if _proxy:
        _opener = urllib.request.build_opener(urllib.request.ProxyHandler({"https": _proxy, "http": _proxy}))
    else:
        _opener = urllib.request.build_opener()
    return _opener


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    opener = _build_opener()
    with opener.open(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode())


def _poster(path: str | None) -> str:
    if not path:
        return ""
    return IMAGE_BASE + path


def search(api_key: str, query: str, page: int = 1, language: str = "zh-CN") -> list[dict]:
    q = urllib.parse.quote(query)
    url = f"{BASE}/search/multi?api_key={api_key}&query={q}&page={page}&language={language}"
    data = _get(url)
    results = []
    for r in data.get("results", []):
        mt = r.get("media_type")
        if mt not in ("movie", "tv"):
            continue
        name = r.get("title") or r.get("name") or ""
        date = r.get("release_date") or r.get("first_air_date") or ""
        results.append({
            "id": r["id"],
            "media_type": mt,
            "name": name,
            "release_date": date[:4] if date else "",
        })
    return results


def get_movie(api_key: str, movie_id: int, language: str = "zh-CN") -> Media:
    url = f"{BASE}/movie/{movie_id}?api_key={api_key}&language={language}"
    data = _get(url)
    genres = [g["name"] for g in data.get("genres", [])]
    release_date = (data.get("release_date") or "")[:4]
    media_type = "Movie" if language.startswith("en-US") else "电影"
    return Media(
        name=data.get("title", ""),
        release_date=release_date,
        media_type=media_type,
        genres=genres,
        poster_url=_poster(data.get("poster_path")),
        seasons=[],
        tmdb_id=movie_id,
        tmdb_media_type="movie",
    )


def get_tv(api_key: str, tv_id: int, language: str = "zh-CN") -> Media:
    url = f"{BASE}/tv/{tv_id}?api_key={api_key}&language={language}"
    data = _get(url)
    genres = [g["name"] for g in data.get("genres", [])]
    release_date = (data.get("first_air_date") or "")[:4]
    media_type = "TV" if language.startswith("en-US") else "剧集"
    seasons_data = data.get("seasons", [])
    seasons = []
    for s in seasons_data:
        if s.get("season_number", 0) < 0:
            continue
        snum = s["season_number"]
        sname = s.get("name") or ("Season " + str(snum) if language.startswith("en-US") else f"第{snum}季")
        episodes = []
        try:
            surl = f"{BASE}/tv/{tv_id}/season/{snum}?api_key={api_key}&language={language}"
            sdata = _get(surl)
            for ep in sdata.get("episodes", []):
                episodes.append(Episode(number=ep.get("episode_number", 0), name=ep.get("name") or ""))
        except Exception:
            pass
        seasons.append(Season(number=snum, name=sname, episodes=episodes))
    return Media(
        name=data.get("name", ""),
        release_date=release_date,
        media_type=media_type,
        genres=genres,
        poster_url=_poster(data.get("poster_path")),
        seasons=seasons,
        tmdb_id=tv_id,
        tmdb_media_type="tv",
    )


def get_media(api_key: str, tmdb_id: int, media_type: str, language: str = "zh-CN") -> Media:
    if media_type == "movie":
        return get_movie(api_key, tmdb_id, language)
    return get_tv(api_key, tmdb_id, language)
