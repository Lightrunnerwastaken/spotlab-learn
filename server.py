"""Lokaler Server zum Schreiben am Kurs: liefert web/ aus, kurs.json immer frisch.

Start:  python server.py            (mit dem Python, in dem spotlab installiert ist)
Dann:   http://127.0.0.1:5200

Der Schülercode läuft NICHT hier, sondern im Browser (Pyodide, siehe
motor/kursmotor.py und web/motor.js) — genau wie auf Vercel. Dieser Server
baut beim Start einmal alles (`baue.py`) und liest danach die Kapitel bei jedem
Laden neu, damit man beim Schreiben nur die Seite neu laden muss.
Nach Änderungen am Kursmotor oder an spotlab: neu starten (oder `python baue.py`).
"""

from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import baue
import kursparser

PORT = int(os.environ.get("SPOTLAB_KURS_PORT", "5200"))


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
                      ".js": "text/javascript", ".json": "application/json", ".zip": "application/zip"}

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(baue.WEB), **kw)

    def log_message(self, fmt, *args):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if urlparse(self.path).path == "/kurs.json":
            try:
                daten, code = kursparser.kurs_lesen(), 200
            except kursparser.KursFehler as f:
                daten, code = {"fehler": str(f)}, 500
            roh = json.dumps(daten, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(roh)))
            self.end_headers()
            self.wfile.write(roh)
            return
        super().do_GET()


def main():
    baue.main()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Spot-Kurs läuft: http://127.0.0.1:{PORT}  (Strg-C beendet)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
