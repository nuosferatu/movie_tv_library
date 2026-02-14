from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Episode:
    number: int
    name: str


@dataclass
class Season:
    number: int
    name: str
    episodes: list[Episode] = field(default_factory=list)


@dataclass
class Media:
    name: str
    release_date: str
    media_type: str  # 电影 / 剧集
    genres: list[str] = field(default_factory=list)  # 剧情、科幻、动画、爱情等
    poster_url: str = ""
    seasons: list[Season] = field(default_factory=list)
    tmdb_id: Optional[int] = None
    tmdb_media_type: Optional[str] = None  # movie / tv

    def to_dict(self):
        return {
            "name": self.name,
            "release_date": self.release_date,
            "media_type": self.media_type,
            "genres": self.genres,
            "poster_url": self.poster_url,
            "seasons": [
                {
                    "number": s.number,
                    "name": s.name,
                    "episodes": [{"number": e.number, "name": e.name} for e in s.episodes],
                }
                for s in self.seasons
            ],
            "tmdb_id": self.tmdb_id,
            "tmdb_media_type": self.tmdb_media_type,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Media":
        seasons = [
            Season(
                number=s["number"],
                name=s["name"],
                episodes=[Episode(number=e["number"], name=e["name"]) for e in s.get("episodes", [])],
            )
            for s in d.get("seasons", [])
        ]
        return cls(
            name=d["name"],
            release_date=d.get("release_date", ""),
            media_type=d.get("media_type", "电影"),
            genres=d.get("genres", []),
            poster_url=d.get("poster_url", ""),
            seasons=seasons,
            tmdb_id=d.get("tmdb_id"),
            tmdb_media_type=d.get("tmdb_media_type"),
        )
