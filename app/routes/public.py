from flask import Blueprint, request, jsonify
import json
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import quote

public_bp = Blueprint("public", __name__)

OL_BASE = "https://openlibrary.org"


def _fetch(url, timeout=12):
    req = Request(url, headers={"User-Agent": "PageTurnApp/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


@public_bp.route("/books", methods=["GET"])
def search_books():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"books": [], "count": 0})

    limit = min(int(request.args.get("limit", 10) or 10), 40)
    offset = int(request.args.get("offset", 0) or 0)

    try:
        data = _fetch(
            f"{OL_BASE}/search.json?q={quote(q)}&limit={limit}&offset={offset}&fields=key,title,author_name,cover_i,first_publish_year,isbn"
        )
    except (URLError, HTTPError, ValueError, TimeoutError) as e:
        return jsonify({"error": f"Open Library unreachable: {e}", "books": []}), 502

    books = []
    for doc in data.get("docs") or []:
        cover_id = doc.get("cover_i")
        books.append(
            {
                "id": doc.get("key", "").replace("/works/", ""),
                "title": doc.get("title") or "Untitled",
                "author": (doc.get("author_name") or ["Unknown"])[0],
                "cover_url": f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None,
                "published_year": doc.get("first_publish_year"),
                "isbn": (doc.get("isbn") or [None])[0],
            }
        )
    return jsonify({"books": books, "count": data.get("numFound", len(books))})


@public_bp.route("/books/<work_id>", methods=["GET"])
def get_work(work_id):
    work_id = work_id.replace("/works/", "").strip()
    try:
        data = _fetch(f"{OL_BASE}/works/{work_id}.json")
    except (URLError, HTTPError, ValueError, TimeoutError) as e:
        return jsonify({"error": str(e)}), 502

    authors = []
    for a in data.get("authors") or []:
        key = (a.get("author") or {}).get("key", "")
        if key:
            try:
                ad = _fetch(f"{OL_BASE}{key}.json")
                authors.append(ad.get("name", "Unknown"))
            except Exception:
                authors.append("Unknown")

    covers = data.get("covers") or []
    cover_url = f"https://covers.openlibrary.org/b/id/{covers[0]}-L.jpg" if covers else None

    description = data.get("description")
    if isinstance(description, dict):
        description = description.get("value")

    return jsonify(
        {
            "book": {
                "id": work_id,
                "title": data.get("title"),
                "author": ", ".join(authors) if authors else "Unknown",
                "description": description,
                "cover_url": cover_url,
                "subjects": (data.get("subjects") or [])[:12],
            }
        }
    )


@public_bp.route("/authors/<author_id>", methods=["GET"])
def get_author(author_id):
    author_id = author_id.replace("/authors/", "").strip()
    try:
        data = _fetch(f"{OL_BASE}/authors/{author_id}.json")
    except (URLError, HTTPError, ValueError, TimeoutError) as e:
        return jsonify({"error": str(e)}), 502
    return jsonify({"author": {"id": author_id, "name": data.get("name"), "bio": data.get("bio")}})