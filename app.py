#!/usr/bin/env python3
import json
import os
from model import Media
from storage import load_starred, add_star
from tmdb import search, get_media

API_KEY = "8be30c3014e32213e2ad4d6f7aca735d"
PAGE_SIZE = 8
LOCALES_DIR = os.path.join(os.path.dirname(__file__), "locales")

lang = "en-US"
T = {}


def load_locales():
    global T, lang
    T = {}
    for name in os.listdir(LOCALES_DIR):
        if not name.endswith(".json"):
            continue
        print("Found locale file:", name)

        path = os.path.join(LOCALES_DIR, name)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        locale_code = data.get("locale")
        if not locale_code:
            print("  No locale code found in", name)
            continue  # Skip if locale code is not found

        print("  Locale Code:", locale_code)
        T[locale_code] = data

    if T and lang not in T:
        default_lang = sorted(T.keys())[0]
        print(f"Language {lang} not found, set to default: {default_lang}")
        lang = default_lang  # Set default language if not found


def t(key: str, **kwargs) -> str:
    s = T[lang][key]
    return s.format(**kwargs) if kwargs else s


def clear():
    # os.system("clear")
    pass


def tmdb_lang():
    global lang
    return lang


def menu():
    clear()
    print()
    print(t("menu_title"))
    print()
    print(t("menu_1"))
    print(t("menu_2"))
    print(t("menu_3"))
    print()
    print(t("menu_hint"))
    print()
    
    while True:
        line = input("> ").strip()
        if line == "-":
            return line
        if line.isdigit() and 1 <= int(line) <= 3:
            return line.strip()


def language_menu():
    global lang
    clear()
    print()
    print(t("lang_title"))
    print()
    locales = sorted(T.keys())
    for i, loc in enumerate(locales, 1):
        print(f"({i}) {T[loc]['lang_name']}")
    print()
    print(t("menu_hint"))
    print()

    while True:
        line = input("> ").strip()
        if line == "-":
            return
        if line.isdigit() and 1 <= int(line) <= len(locales):
            lang = locales[int(line) - 1]
            break


def star_list():
    starred = load_starred()
    page = 0
    while True:
        clear()
        print()
        print(t("star_title"))
        print()
        start = page * PAGE_SIZE
        chunk = starred[start : start + PAGE_SIZE]
        for i, (media, _) in enumerate(chunk):
            print(f"  {i + 1}. {media.name}  ({media.release_date})")
        total = len(starred)
        pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        print()
        print(t("page_info", page=page + 1, pages=pages, total=total))
        print(t("star_hint"))
        print()
        line = input("> ").strip()
        if line == "-":
            return
        if line == "p" and page > 0:
            page -= 1
            continue
        if line == "n" and page < pages - 1:
            page += 1
            continue
        if line in "12345678":
            idx = page * PAGE_SIZE + (ord(line) - ord("1"))
            if idx < total:
                star_detail(starred[idx][0], starred[idx][1])
                starred = load_starred()


def star_detail(media: Media, star_date: str):
    while True:
        clear()
        print()
        print(t("detail_title"))
        print()
        print(t("detail_name"), media.name)
        print(t("detail_date"), media.release_date)
        print(t("detail_type"), media.media_type)
        print(t("detail_genre"), "、".join(media.genres) if media.genres else "-")
        print(t("detail_poster"), media.poster_url or "-")
        print(t("detail_star_date"), star_date)
        print()
        print(t("detail_seasons"))
        for s in media.seasons:
            print(t("season_ep", n=s.number, name=s.name, count=len(s.episodes)))
            for e in s.episodes[:20]:
                print(t("episode_line", e=e.number, name=e.name))
        if not media.seasons and (media.media_type == "电影" or media.media_type == "Movie"):
            print(t("no_episodes"))
        print()
        print(t("detail_hint"))
        print()
        if input("> ").strip() == "-":
            return


def search_flow():
    clear()
    print()
    print(t("search_title"))
    print()
    print(t("search_hint"))
    print()
    q = input("> ").strip()
    if q == "-":
        return
    try:
        results = search(API_KEY, q, page=1, language=tmdb_lang())
    except Exception:
        return
    page = 0
    search_page_results = results
    last_fetched_page = 1
    while True:
        clear()
        print()
        print(t("search_results_title"))
        print()
        start = page * PAGE_SIZE
        need = start + PAGE_SIZE
        if need > len(search_page_results) and last_fetched_page > 0:
            try:
                more = search(API_KEY, q, page=last_fetched_page + 1, language=tmdb_lang())
                search_page_results.extend(more)
                last_fetched_page += 1
            except Exception:
                pass
        chunk = search_page_results[start : start + PAGE_SIZE]
        for i, r in enumerate(chunk):
            print(f"  {i + 1}. {r['name']}  ({r['release_date']})")
        total = len(search_page_results)
        pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        print()
        print(t("page_info", page=page + 1, pages=pages, total=total))
        print(t("search_result_hint"))
        print()
        line = input("> ").strip()
        if line == "-":
            return
        if line == "p" and page > 0:
            page -= 1
            continue
        if line == "n":
            if page < pages - 1:
                page += 1
            else:
                try:
                    more = search(API_KEY, q, page=last_fetched_page + 1, language=tmdb_lang())
                    search_page_results.extend(more)
                    last_fetched_page += 1
                    if more:
                        page += 1
                except Exception:
                    pass
            continue
        if line in "12345678":
            idx = page * PAGE_SIZE + (ord(line) - ord("1"))
            if idx < len(search_page_results):
                r = search_page_results[idx]
                try:
                    media = get_media(API_KEY, r["id"], r["media_type"], tmdb_lang())
                    search_detail(media)
                except Exception:
                    pass
            continue
        if line.startswith("s "):
            parts = line[2:].strip().split()
            if parts and parts[0] in "12345678":
                idx = page * PAGE_SIZE + (ord(parts[0]) - ord("1"))
                if idx < len(search_page_results):
                    r = search_page_results[idx]
                    try:
                        media = get_media(API_KEY, r["id"], r["media_type"], tmdb_lang())
                        add_star(media)
                    except Exception:
                        pass


def search_detail(media: Media):
    while True:
        clear()
        print()
        print(t("search_detail_title"))
        print()
        print(t("detail_name"), media.name)
        print(t("detail_date"), media.release_date)
        print(t("detail_type"), media.media_type)
        print(t("detail_genre"), "、".join(media.genres) if media.genres else "-")
        print(t("detail_poster"), media.poster_url or "-")
        print()
        print(t("detail_seasons"))
        for s in media.seasons:
            print(t("season_ep", n=s.number, name=s.name, count=len(s.episodes)))
            for e in s.episodes[:20]:
                print(t("episode_line", e=e.number, name=e.name))
        if not media.seasons and (media.media_type == "电影" or media.media_type == "Movie"):
            print(t("no_episodes"))
        print()
        print(t("search_detail_hint"))
        print()
        line = input("> ").strip()
        if line == "-":
            return
        if line == "s":
            add_star(media)
            return


def main():
    global lang
    load_locales()
    while True:
        choice = menu()
        if choice == "1":
            star_list()
        elif choice == "2":
            search_flow()
        elif choice == "3":
            language_menu()
        elif choice == "-":
            break


if __name__ == "__main__":
    main()
