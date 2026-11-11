"""Der Kursmotor: führt Schülercode mit dem ECHTEN spotlab-Simulator aus — ohne Server.

Läuft im Browser (Pyodide in einem Web Worker) und genauso in gewöhnlichem
Python (der Prüflauf `tests/kurs_pruefen.py`). Beide Wege nehmen diese Datei,
damit der Prüflauf prüft, was die Schüler bekommen.

Drei Eingriffe machen spotlab browsertauglich, ohne spotlab zu ändern:

1. **Virtuelle Uhr.** `time.sleep(2)` stellt die Uhr um 2 s vor, statt zu
   warten. Der Simulator rechnet in kleinen Schritten bis zur aktuellen Zeit
   (`MAX_DT_S`), ihm ist egal, wie schnell die Uhr läuft. Ein Lauf von 50 s ist
   so in einer Sekunde fertig; die Seite spielt den Weg danach ab.
2. **Abtaster ohne Thread.** spotlab zeichnet den Zustand in einem eigenen
   Faden mit 10 Hz auf. Im Browser gibt es keine Fäden; hier tastet die Uhr
   bei jedem Vorstellen ab, im selben Takt. `zustand.jsonl` sieht aus wie immer.
3. **Attrappen** für Pakete, die nur der echte Roboter braucht (grpc für die
   Netzverbindung, cryptography, urllib3 ...). Sie nehmen jeden Zugriff an.
   Im Simulator wird keiner davon je benutzt.

Sicherheit: `SPOTLAB_NUR_TROCKEN=1` vor dem ersten Import von spotlab — dann
weist spotlab jedes Backend ab, das einen Roboter erreichen kann.
"""

from __future__ import annotations

import contextlib
import importlib.abc
import importlib.machinery
import io
import json
import math
import os
import re
import sys
import tempfile
import time
import traceback
import types
from pathlib import Path

# Nur für die Verbindung zum echten Roboter (Netz, Anmeldung, Schlüsselbund).
ATTRAPPEN = ("grpc", "cryptography", "urllib3", "requests", "pynmea2", "keyring", "jwt")
GRENZE_S = 600.0          # virtuelle Sekunden je Lauf, dann ist Schluss
TAKT_S = 0.02             # so fein stellt sleep die Uhr vor


# ================================================================ Attrappen

class _Irgendwas:
    """Nimmt jeden Zugriff an: Attribut, Aufruf, Erben, Vergleich."""

    def __init__(self, *a, **k):
        pass

    def __call__(self, *a, **k):
        return _Irgendwas()

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        return _Irgendwas()

    def __mro_entries__(self, bases):
        return (object,)

    def __iter__(self):
        return iter(())

    def __bool__(self):
        return False


class _AttrappenFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, name, path=None, target=None):
        oben = name.split(".")[0]
        if oben in ATTRAPPEN:
            # Nur, wenn es das echte Paket nicht gibt: in gewöhnlichem Python
            # nimmt spotlab dann dieselben Pakete wie immer.
            if oben == name and _gibt_es_echt(name):
                return None
            if oben != name and oben not in _ATTRAPPEN_AKTIV:
                return None
            _ATTRAPPEN_AKTIV.add(oben)
            return importlib.machinery.ModuleSpec(name, self, is_package=True)
        return None

    def create_module(self, spec):
        modul = types.ModuleType(spec.name)
        modul.__getattr__ = lambda attr: _Irgendwas()
        modul.__path__ = []
        return modul

    def exec_module(self, module):
        pass


_ATTRAPPEN_AKTIV: set[str] = set()


def _gibt_es_echt(name):
    for finder in sys.meta_path:
        if isinstance(finder, _AttrappenFinder):
            continue
        try:
            if finder.find_spec(name, None) is not None:
                return True
        except (AttributeError, ImportError, ValueError):
            continue
    return False


# ================================================================ Uhr

class Zeitlimit(BaseException):
    """BaseException: ein `except Exception` im Schülercode darf sie nicht schlucken."""


class Uhr:
    def __init__(self):
        self.null = _ECHT["time"]()
        self.v = 0.0                 # virtuelle Sekunden seit dem Start
        self.grenze = None
        self.haken = []              # bei jedem Vorstellen gerufen

    def _tick(self):
        # Jedes Ablesen schiebt die Uhr um eine Mikrosekunde: eine Schleife, die
        # ohne sleep auf eine Zeit wartet, käme sonst nie an.
        self.v += 1e-6

    def time(self):
        self._tick()
        return self.null + self.v

    def time_ns(self):
        return int(self.time() * 1e9)

    def monotonic(self):
        self._tick()
        return 1000.0 + self.v

    def monotonic_ns(self):
        return int(self.monotonic() * 1e9)

    def sleep(self, sekunden):
        sekunden = float(sekunden)
        if sekunden < 0:
            raise ValueError("sleep length must be non-negative")
        ende = self.v + sekunden
        while self.v < ende:
            self.v = min(ende, self.v + TAKT_S)
            for haken in list(self.haken):
                haken()
            if self.grenze is not None and self.v > self.grenze:
                self.grenze = None   # nur EINMAL werfen: der Abbau schläft auch
                raise Zeitlimit()


_ECHT = {"time": time.time, "monotonic": time.monotonic, "sleep": time.sleep,
         "perf_counter": time.perf_counter}
UHR: Uhr | None = None
_ABTASTER: list = []


def _abtasten():
    jetzt = UHR.monotonic()
    for abtaster in list(_ABTASTER):
        if jetzt >= abtaster._kurs_naechste:
            abtaster._einmal(abtaster._reich)
            abtaster._kurs_naechste = jetzt + abtaster._periode


def installieren():
    """Einmal je Prozess, VOR dem ersten Import von spotlab."""
    global UHR
    if UHR is not None:
        return
    os.environ["SPOTLAB_NUR_TROCKEN"] = "1"
    os.environ["SPOTLAB_BACKEND"] = "sim"
    sys.meta_path.insert(0, _AttrappenFinder())

    UHR = Uhr()
    time.time = UHR.time
    time.time_ns = UHR.time_ns
    time.monotonic = UHR.monotonic
    time.monotonic_ns = UHR.monotonic_ns
    time.perf_counter = UHR.monotonic
    time.sleep = UHR.sleep
    UHR.haken.append(_abtasten)

    from spotlab.record import sampler

    def start(self):
        if self in _ABTASTER:
            return
        self._kurs_naechste = UHR.monotonic()
        _ABTASTER.append(self)
        self._einmal(self._reich)

    def stop(self, timeout=2.0):
        if self in _ABTASTER:
            self._einmal(self._reich)
            _ABTASTER.remove(self)

    sampler.StateSampler.start = start
    sampler.StateSampler.stop = stop


# ================================================================ Laufen

def lauf(code: str, raum: str = "leer", start: str = "", grenze_s: float = GRENZE_S) -> dict:
    """Führt `code` im Simulator aus und gibt zurück, was die Seite braucht."""
    installieren()
    ordner = Path(tempfile.mkdtemp(prefix="lauf-"))
    programm = ordner / "programm.py"
    programm.write_text(code, encoding="utf-8")

    if raum and raum != "keiner":
        os.environ["SPOTLAB_RAUM"] = raum
    else:
        os.environ.pop("SPOTLAB_RAUM", None)
    os.environ["SPOTLAB_RAUM_START"] = start or ""

    puffer = io.StringIO()
    vorher_ordner = os.getcwd()
    vorher_argv = sys.argv
    beginn = UHR.v
    UHR.grenze = UHR.v + grenze_s
    status = "fertig"
    try:
        os.chdir(ordner)
        sys.argv = [str(programm)]
        with contextlib.redirect_stdout(puffer), contextlib.redirect_stderr(puffer):
            try:
                exec(compile(code, str(programm), "exec"),
                     {"__name__": "__main__", "__file__": str(programm)})
            except SystemExit as ende:
                if ende.code not in (None, 0):
                    status = "fehler"
                    print(f"Programm beendet mit sys.exit({ende.code!r})")
            except Zeitlimit:
                status = "abgebrochen"
                print(f"\n[nach {grenze_s:.0f} s Spot-Zeit automatisch angehalten]")
            except BaseException:   # noqa: BLE001 — jeder Fehler gehört dem Schüler
                status = "fehler"
                traceback.print_exc()
    finally:
        UHR.grenze = None
        _ABTASTER.clear()
        os.chdir(vorher_ordner)
        sys.argv = vorher_argv

    lauf_ordner = _lauf_ordner(ordner)
    ausgabe = puffer.getvalue()
    ereignisse = _jsonl(lauf_ordner / "ereignisse.jsonl") if lauf_ordner else []
    weg = _weg(lauf_ordner) if lauf_ordner else []
    angestossen = [e.get("daten", {}) for e in ereignisse if e.get("art") == "angestossen"]
    fehler = fehler_kurz(ausgabe) if status == "fehler" else None
    if fehler and angestossen and "abgelaufen" in fehler["meldung"]:
        # spotlab sagt hier nur „abgelaufen“ (BEFUNDE_SPOTLAB.md, Befund 2);
        # die Aufzeichnung weiss, woran Spot hängen geblieben ist.
        d = angestossen[-1]
        fehler["hinweis"] = (f"Spot ist bei x = {d.get('x', 0):.2f}, y = {d.get('y', 0):.2f} "
                             f"an «{d.get('hindernis', 'ein Hindernis')}» gestossen und kam nicht weiter.")
    return {
        "start": start or "",
        "status": status,
        "ausgabe": ausgabe,
        "fehler": fehler,
        "weg": weg,
        "angestossen": [[d.get("x"), d.get("y")] for d in angestossen],
        "kommandos": [e.get("daten", {}).get("name") for e in ereignisse if e.get("art") == "kommando"],
        "dauer": round(UHR.v - beginn, 1),
    }


def lauf_mit_pruefung(code, raum, start, ziele=None):
    ergebnis = lauf(code, raum, start)
    ergebnis["pruefung"] = pruefen(ziele, ergebnis) if ziele else None
    return ergebnis


def lauf_json(auftrag_json: str) -> str:
    """Einstieg für den Browser: JSON hinein, JSON heraus."""
    a = json.loads(auftrag_json)
    return json.dumps(lauf_mit_pruefung(a.get("code", ""), a.get("raum", "leer"),
                                        a.get("start", ""), a.get("ziele")), ensure_ascii=False)


def _lauf_ordner(ordner: Path):
    runs = ordner / "runs"
    if not runs.is_dir():
        return None
    kandidaten = sorted(p for p in runs.iterdir() if p.is_dir())
    return kandidaten[-1] if kandidaten else None


def _jsonl(pfad: Path) -> list:
    if not pfad.exists():
        return []
    liste = []
    for zeile in pfad.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            liste.append(json.loads(zeile))
        except ValueError:
            continue
    return liste


def _weg(lauf_ordner: Path) -> list:
    """[[t, x, y, blick_grad], ...] aus zustand.jsonl."""
    punkte = []
    for d in _jsonl(lauf_ordner / "zustand.jsonl"):
        try:
            x, y, gier = d["daten"]["pose"]
        except (KeyError, TypeError, ValueError):
            continue
        punkte.append([round(d["t"], 2), round(x, 3), round(y, 3), round(math.degrees(gier), 1)])
    return punkte


# ================================================================ Auswerten

def fehler_kurz(text: str) -> dict | None:
    """Aus einem Traceback: die Zeile im Schülerprogramm und die eigentliche Meldung."""
    if "Traceback" not in text:
        return None
    zeilen = text.rstrip().splitlines()
    zeile_nr, code_zeile = None, None
    for i, z in enumerate(zeilen):
        m = re.search(r'File ".*programm\.py", line (\d+)', z)
        if m:
            zeile_nr = int(m.group(1))
            naechste = zeilen[i + 1].strip() if i + 1 < len(zeilen) else ""
            code_zeile = naechste if naechste and not naechste.startswith("File ") else None
    meldung = zeilen[-1].strip()
    for z in reversed(zeilen):
        if re.match(r"^\w+(\.\w+)*(Error|Exception|Warning|Capability|Lost|Missing|Rejected|Powered)\b", z.strip()) \
                or re.match(r"^\w+(\.\w+)*: ", z.strip()):
            meldung = z.strip()
            break
    return {"zeile": zeile_nr, "code": code_zeile, "meldung": meldung}


def _winkel_abstand(a, b):
    return abs((a - b + 180) % 360 - 180)


def pruefen(ziele: list, e: dict) -> list:
    """Jedes Ziel einer Aufgabe gegen ein Laufergebnis. Erste Zeile immer: lief es durch?"""
    weg = e["weg"]
    lage = weg[-1] if weg else None
    fertig = e["status"] == "fertig"
    ergebnis = [{"text": "Das Programm läuft ohne Fehler bis zum Ende", "ok": fertig,
                 "detail": "" if fertig else "Es ist mit einem Fehler stehen geblieben oder wurde angehalten."}]
    for ziel in ziele:
        art, w = ziel["art"], ziel["werte"]
        if art == "ende_bei":
            text = f"Spot endet bei x = {w[0]:g}, y = {w[1]:g} (± {w[2]:g} m)"
            if lage is None:
                ok, detail = False, "Spot hat sich nicht bewegt."
            else:
                d = math.hypot(lage[1] - w[0], lage[2] - w[1])
                ok, detail = d <= w[2], f"Er endet bei x = {lage[1]:.2f}, y = {lage[2]:.2f}, also {d:.2f} m daneben."
        elif art == "ende_in":
            x1, y1, x2, y2 = w
            text = f"Spot endet im Bereich x {x1:g}–{x2:g}, y {y1:g}–{y2:g}"
            if lage is None:
                ok, detail = False, "Spot hat sich nicht bewegt."
            else:
                ok = x1 <= lage[1] <= x2 and y1 <= lage[2] <= y2
                detail = f"Er endet bei x = {lage[1]:.2f}, y = {lage[2]:.2f}."
        elif art == "blick":
            text = f"Spot schaut am Ende in Richtung {w[0]:g}° (± {w[1]:g}°)"
            if lage is None:
                ok, detail = False, "Kein Zustand aufgezeichnet."
            else:
                ok, detail = _winkel_abstand(lage[3], w[0]) <= w[1], f"Er schaut in Richtung {lage[3]:.0f}°."
        elif art == "nicht_angestossen":
            n = len(e["angestossen"])
            text = "Spot stösst nirgends an"
            ok, detail = n == 0, ("" if n == 0 else f"Er ist {n}-mal angestossen.")
        elif art == "ausgabe":
            text = f"In der Ausgabe steht «{w[0]}»"
            ok, detail = w[0] in e["ausgabe"], ""
        elif art == "aufgerufen":
            text = f"Das Programm benutzt {w[0]}()"
            ok, detail = w[0] in e["kommandos"], ""
        elif art == "gefahren":
            strecke = sum(math.hypot(b[1] - a[1], b[2] - a[2]) for a, b in zip(weg, weg[1:]))
            text = f"Spot legt mindestens {w[0]:g} m zurück"
            ok, detail = strecke >= w[0], f"Er ist {strecke:.2f} m gegangen."
        elif art in ("steht", "sitzt"):
            haltung = None
            for k in e["kommandos"]:
                if k == "stand":
                    haltung = "steht"
                elif k in ("sit", "power_off"):
                    haltung = "sitzt"
            text = "Spot steht am Ende" if art == "steht" else "Spot sitzt am Ende"
            ok = haltung == art
            detail = "" if ok else ("Er hat nie stand() bekommen." if haltung is None else f"Er {haltung} am Ende.")
        else:
            continue
        ergebnis.append({"text": text, "ok": bool(ok), "detail": detail})
    return ergebnis


# ================================================================ Räume

def raum_als_json(name: str) -> dict:
    from spotlab.welt.raum import raum_laden

    r = raum_laden(name)
    return {
        "name": r.name,
        "beschreibung": r.beschreibung,
        "groesse": list(r.groesse) if r.groesse else None,
        "start": list(r.start),
        "waende": [[w.x1, w.y1, w.x2, w.y2] for w in r.waende],
        "bloecke": [{"name": b.name, "ecken": [list(p) for p in b.ecken()]} for b in r.bloecke],
        "boeden": [{"name": b.name, "art": b.art, "ecken": [list(p) for p in b.ecken()]} for b in r.boeden],
        "sperrzonen": [{"name": s.name, "ecken": [list(p) for p in s.ecken()]} for s in r.sperrzonen],
        "tags": [{"id": t.id, "x": t.x, "y": t.y, "grad": t.grad} for t in r.tags],
    }
