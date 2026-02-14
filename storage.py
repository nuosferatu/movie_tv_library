import json
from datetime import datetime
from pathlib import Path
from model import Media

STAR_FILE = Path(__file__).parent / "starred.json"


def load_starred() -> list[tuple[Media, str]]:
    if not STAR_FILE.exists():
        return []
    with open(STAR_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    out = []
    for item in raw:
        star_date = item.get("star_date", "")
        media = Media.from_dict({k: v for k, v in item.items() if k != "star_date"})
        out.append((media, star_date))
    return out


def save_starred(items: list[tuple[Media, str]]) -> None:
    raw = []
    for media, star_date in items:
        d = media.to_dict()
        d["star_date"] = star_date
        raw.append(d)
    with open(STAR_FILE, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)


def add_star(media: Media) -> None:
    items = load_starred()
    star_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    for m, _ in items:
        if m.tmdb_id == media.tmdb_id and m.tmdb_media_type == media.tmdb_media_type:
            return
    items.insert(0, (media, star_date))
    save_starred(items)


def remove_star_by_tmdb(tmdb_id: int, tmdb_media_type: str) -> None:
    items = [(m, d) for m, d in load_starred() if m.tmdb_id != tmdb_id or m.tmdb_media_type != tmdb_media_type]
    save_starred(items)
