"""Immutable local research exchange, version history and read-only discovery."""

import html
import json
import re
import shutil
import sqlite3
import tempfile
from contextlib import closing, contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .experiments import digest, json_bytes, load
from .models import OpenReproError
from .packages import import_experiment

SHA256 = re.compile(r"^[a-f0-9]{64}$")


@contextmanager
def database(catalog: Path):
    catalog = Path(catalog)
    if catalog.is_symlink():
        raise OpenReproError("Catalog symlinks are forbidden")
    catalog.mkdir(parents=True, exist_ok=True)
    db_path = catalog / "catalog.sqlite3"
    if db_path.is_symlink() or (catalog / "packages").is_symlink():
        raise OpenReproError("Catalog symlinks are forbidden")
    with closing(sqlite3.connect(db_path, timeout=10)) as connection:
        with connection:
            connection.row_factory = sqlite3.Row
            connection.execute("""CREATE TABLE IF NOT EXISTS packages (
                sha256 TEXT PRIMARY KEY, experiment TEXT NOT NULL, revision INTEGER NOT NULL,
                title TEXT NOT NULL, description TEXT NOT NULL, authors TEXT NOT NULL,
                license TEXT NOT NULL, doi TEXT, keywords TEXT NOT NULL, created TEXT NOT NULL,
                UNIQUE(experiment, revision))""")
            yield connection


def publish_package(package: Path, catalog: Path) -> dict:
    package, catalog = Path(package), Path(catalog)
    with (
        database(catalog) as db,
        tempfile.TemporaryDirectory(prefix=".publish-", dir=catalog) as directory,
    ):
        staging = Path(directory)
        copied = staging / "package.orepro"
        shutil.copyfile(package, copied)
        checksum = digest(copied)
        root = import_experiment(copied, staging / "validated")
        manifest = load(root)
        db.execute("BEGIN IMMEDIATE")
        existing = db.execute("SELECT * FROM packages WHERE sha256=?", (checksum,)).fetchone()
        if existing:
            blob = catalog / "packages" / (checksum + ".orepro")
            if blob.is_symlink() or not blob.is_file() or digest(blob) != checksum:
                raise OpenReproError("Catalog package integrity failure")
            return _record(existing)
        revision = db.execute(
            "SELECT COALESCE(MAX(revision),0)+1 FROM packages WHERE experiment=?",
            (str(manifest.identifier),),
        ).fetchone()[0]
        blobs = catalog / "packages"
        blobs.mkdir(exist_ok=True)
        target = blobs / (checksum + ".orepro")
        if target.exists():
            if target.is_symlink() or digest(target) != checksum:
                raise OpenReproError("Catalog blob integrity failure")
        else:
            created_blob = False
            try:
                with copied.open("rb") as source, target.open("xb") as output:
                    created_blob = True
                    shutil.copyfileobj(source, output)
            except BaseException:
                if created_blob:
                    target.unlink(missing_ok=True)
                raise
        db.execute(
            "INSERT INTO packages VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                checksum,
                str(manifest.identifier),
                revision,
                manifest.title,
                manifest.description,
                json.dumps(manifest.authors),
                manifest.license,
                manifest.doi,
                json.dumps(manifest.keywords),
                manifest.created.isoformat(),
            ),
        )
        return _record(db.execute("SELECT * FROM packages WHERE sha256=?", (checksum,)).fetchone())


def _record(row):
    value = dict(row)
    value["authors"] = json.loads(value["authors"])
    value["keywords"] = json.loads(value["keywords"])
    value["identifier"] = "urn:sha256:" + value["sha256"]
    return value


def search_catalog(
    catalog: Path, query: str = "", *, limit: int = 20, experiment: str | None = None
) -> list[dict]:
    if len(query) > 200 or not 1 <= limit <= 100:
        raise OpenReproError("Query length or result limit exceeded")
    pattern = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    with database(catalog) as db:
        rows = db.execute(
            """SELECT * FROM packages WHERE
            (title LIKE ? ESCAPE '\\' OR description LIKE ? ESCAPE '\\'
             OR authors LIKE ? ESCAPE '\\'
             OR keywords LIKE ? ESCAPE '\\') AND (? IS NULL OR experiment=?)
            ORDER BY experiment, revision DESC LIMIT ?""",
            (pattern, pattern, pattern, pattern, experiment, experiment, limit),
        ).fetchall()
    return [_record(row) for row in rows]


def package_path(catalog: Path, checksum: str) -> Path:
    if not SHA256.fullmatch(checksum):
        raise OpenReproError("Use a complete SHA-256 identifier")
    with database(catalog) as db:
        if not db.execute("SELECT 1 FROM packages WHERE sha256=?", (checksum,)).fetchone():
            raise OpenReproError("Package not found")
    path = Path(catalog) / "packages" / (checksum + ".orepro")
    if path.is_symlink() or not path.is_file() or digest(path) != checksum:
        raise OpenReproError("Catalog package integrity failure")
    return path


def fetch_package(catalog: Path, checksum: str, destination: Path) -> dict:
    path = package_path(catalog, checksum)
    root = import_experiment(path, destination)
    return {"workspace": str(root), "identifier": "urn:sha256:" + checksum}


def citation(catalog: Path, checksum: str) -> dict:
    package_path(catalog, checksum)
    with database(catalog) as db:
        record = _record(
            db.execute("SELECT * FROM packages WHERE sha256=?", (checksum,)).fetchone()
        )
    result = {
        "type": "dataset",
        "id": record["identifier"],
        "title": record["title"],
        "author": [{"literal": name} for name in record["authors"]],
        "version": str(record["revision"]),
        "issued": {"date-parts": [[int(record["created"][:4])]]},
        "note": "OpenRepro package SHA-256: " + checksum,
    }
    if record["doi"]:
        result["DOI"] = record["doi"]
    return result


def catalog_server(catalog: Path, host="127.0.0.1", port=8080) -> ThreadingHTTPServer:
    """Serve only catalog search and verified packages; no upload or execution routes."""
    catalog = Path(catalog)
    with database(catalog):
        pass

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def log_message(self, *_args):
            pass

        def reply(self, content, content_type, status=200):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'"
            )
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self):
            route = urlsplit(self.path)
            try:
                if route.path == "/search":
                    query = parse_qs(route.query)
                    values = search_catalog(
                        catalog,
                        query.get("q", [""])[0],
                        limit=int(query.get("limit", ["20"])[0]),
                        experiment=query.get("experiment", [None])[0],
                    )
                    self.reply(json_bytes({"packages": values}), "application/json")
                elif route.path.startswith("/packages/"):
                    checksum = route.path.removeprefix("/packages/").removesuffix(".orepro")
                    path = package_path(catalog, checksum)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/zip")
                    self.send_header(
                        "Content-Disposition", f'attachment; filename="{checksum}.orepro"'
                    )
                    self.send_header("Content-Length", str(path.stat().st_size))
                    self.send_header("ETag", '"' + checksum + '"')
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.end_headers()
                    with path.open("rb") as stream:
                        shutil.copyfileobj(stream, self.wfile)
                elif route.path == "/":
                    items = search_catalog(catalog, parse_qs(route.query).get("q", [""])[0])
                    rows = "".join(
                        '<li><a href="/packages/'
                        + item["sha256"]
                        + '.orepro">'
                        + html.escape(item["title"])
                        + "</a> — revision "
                        + str(item["revision"])
                        + "</li>"
                        for item in items
                    )
                    page = (
                        '<!doctype html><html lang="en"><meta charset="utf-8">'
                        "<title>OpenRepro research catalog</title><h1>Research catalog</h1>"
                        '<form action="/"><label>Search '
                        '<input name="q" maxlength="200"></label>'
                        "<button>Search</button></form><ul>" + rows + "</ul></html>"
                    )
                    self.reply(page.encode(), "text/html; charset=utf-8")
                else:
                    self.reply(b'{"error":"not found"}', "application/json", 404)
            except (ValueError, OSError, sqlite3.Error):
                self.reply(
                    b'{"error":"invalid request or unavailable package"}', "application/json", 400
                )

    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    return server
