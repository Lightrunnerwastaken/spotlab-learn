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


# Der Abtaster schreibt im Kurs höchstens 5 Zustände je Sekunde Spot-Zeit (spotlab:
# 10). Gezeichnet wird daraus nur der Weg; bei 0.5 m/s liegen zwei Punkte 10 cm
# auseinander. Gemessen 11.11.2026: das Schreiben kostete gut die Hälfte der Rechenzeit.
KURS_ABTASTUNG_S = 0.2


def _abtasten():
    jetzt = UHR.monotonic()
    for abtaster in list(_ABTASTER):
        if jetzt >= abtaster._kurs_naechste:
            abtaster._einmal(abtaster._reich)
            abtaster._kurs_naechste = jetzt + max(abtaster._periode, KURS_ABTASTUNG_S)


def installieren():
    """Einmal je Prozess, VOR dem ersten Import von spotlab."""
    global UHR
    if UHR is not None:
        return
    os.environ["SPOTLAB_NUR_TROCKEN"] = "1"
    os.environ["SPOTLAB_BACKEND"] = "sim"
    sys.meta_path.insert(0, _AttrappenFinder())
    # Die Aufzeichnung erzwingt nach jeder Zeile fsync (gegen Datenverlust bei einem
    # Absturz am echten Spot). Ein Kurslauf schreibt in einen Wegwerf-Ordner.
    os.fsync = lambda fd: None

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
    kursraeume_einhaengen()
    trockenlauf_wie_am_geraet()
    kamera_einhaengen()
    mensch_einhaengen()


# ================================================================ Kamera-Szenen
#
# raum=kamera-<name>: Spot steht im 2D-Übungsraum (Lage, look, tags wie immer), und
# die Kameras liefern Antworten, die tools/aufnahmen_bauen.py vorher im 3D-Übungsraum
# von spotlab (MuJoCo) an GENAU dieser Stelle aufgenommen hat: echte ImageResponse-
# Protobufs mit Bild, Tiefe, Kalibrierung und Rahmenbaum. spotlabs Auswertung
# (perception.Image, DepthImage, point_cloud) läuft unverändert darauf. Weil die
# Bilder zu einer festen Stelle gehören, darf Spot in einer Szene nicht gehen.

KURSAUFNAHMEN = Path(__file__).resolve().parent / "kursaufnahmen"
AUFNAHME = None            # {quelle: protobuf-bytes} während eines Szenenlaufs


def szenen() -> dict:
    pfad = KURSAUFNAHMEN / "szenen.json"
    return json.loads(pfad.read_text(encoding="utf-8")) if pfad.exists() else {}


def szene_lesen(name: str) -> dict:
    import gzip
    import struct

    daten, i, aus = gzip.decompress((KURSAUFNAHMEN / f"{name}.bin.gz").read_bytes()), 0, {}
    while i < len(daten):
        (n,) = struct.unpack_from("<I", daten, i); i += 4
        quelle = daten[i:i + n].decode("utf-8"); i += n
        (m,) = struct.unpack_from("<I", daten, i); i += 4
        aus[quelle] = daten[i:i + m]; i += m
    return aus


def kamera_einhaengen():
    from spotlab.api import motion
    from spotlab.backends import sim
    from spotlab.backends.base import Capability
    from spotlab.errors import SpotlabError

    if getattr(sim.SimBackend.images, "_kurs", False):
        return
    cls = sim.SimBackend
    faehig_vorher, quellen_vorher, bilder_vorher = cls.capabilities, cls.image_sources, cls.images

    def capabilities(self):
        koennen = faehig_vorher(self)
        if AUFNAHME:
            koennen |= Capability.DEPTH_CAMERAS | Capability.GRAY_CAMERAS
        return koennen

    def image_sources(self):
        return list(AUFNAHME) if AUFNAHME else quellen_vorher(self)

    def images(self, sources):
        if not AUFNAHME:
            return bilder_vorher(self, sources)
        from bosdyn.api import image_pb2

        antworten = []
        for quelle in sources:
            if quelle not in AUFNAHME:
                raise SpotlabError(f"Unbekannte Bildquelle '{quelle}'. Vorhanden: {', '.join(AUFNAHME)}")
            antwort = image_pb2.ImageResponse()
            antwort.ParseFromString(AUFNAHME[quelle])
            antworten.append(antwort)
        return antworten

    images._kurs = True
    cls.capabilities, cls.image_sources, cls.images = capabilities, image_sources, images

    def gesperrt(vorher):
        def befehl(*args, **kwargs):
            if AUFNAHME:
                raise SpotlabError(
                    "In diesem Kapitel steht Spot still: Die Kamerabilder sind vorher im "
                    "3D-Übungsraum an genau dieser Stelle aufgenommen worden und würden "
                    "nach einem Schritt nicht mehr stimmen.")
            return vorher(*args, **kwargs)
        return befehl

    motion.move, motion.walk = gesperrt(motion.move), gesperrt(motion.walk)


# ================================================================ Ein Mensch geht mit
#
# raum=mensch-<name>: im 2D-Übungsraum geht ein Mensch einen festen Weg und trägt einen
# AprilTag auf dem Rücken. spotlab kennt keine bewegten Dinge; der Kurs schiebt dafür bei
# jeder Tag-Abfrage den Tag an die Stelle, an der der Mensch gerade ist (virtuelle Uhr
# seit connect), und spotlabs eigene Sichtprüfung entscheidet wie immer, ob Spot ihn
# sieht (bis 3 m, freie Sichtlinie, rundum). Der Mensch ist kein Hindernis: Spot kann
# nicht an ihn stossen, das Ziel `mensch_abstand` prüft den Abstand stattdessen.
#
# Weg: Liste [x, y, pause_s] — er geht mit `tempo` von Punkt zu Punkt und wartet an
# jedem Punkt pause_s. Am ersten Punkt steht er `pause_s` lang, bevor er losgeht.

MENSCHEN = {
    "mensch-steht": {
        "titel": "Ein Mensch mit Tag 9 auf dem Rücken steht im Raum",
        "raum": "leer", "start": "1,1.2,0", "tag": 9, "tempo": 0.4,
        "weg": [[2.6, 2.8, 0]],
    },
    "mensch-quer": {
        "titel": "Der Mensch geht vor Spot hin und her",
        "raum": "leer", "start": "1.2,2,0", "tag": 9, "tempo": 0.4,
        "weg": [[3.4, 0.7, 2], [3.4, 3.3, 1], [3.4, 1.6, 0]],
    },
    "mensch-geht": {
        "titel": "Der Mensch geht weg, bleibt stehen und kommt zurück",
        "raum": "leer", "start": "0.7,2,0", "tag": 9, "tempo": 0.4,
        "weg": [[2.5, 2, 3], [4.3, 2.4, 3], [4.3, 3.3, 2], [2.4, 3.0, 0]],
    },
    "mensch-wohnung": {
        "titel": "Der Mensch geht durch zwei Türen in ein anderes Zimmer",
        "raum": "wohnung", "start": "2,0.8,90", "tag": 9, "tempo": 0.4,
        "weg": [[2.2, 2.7, 4], [2.2, 3.6, 0], [3.7, 3.6, 0], [5.9, 3.5, 0],
                [5.9, 1.6, 0], [7.0, 1.3, 0]],
    },
}
MENSCH = None              # Plan während eines Laufs
MENSCH_T0 = 0.0            # virtuelle Zeit beim connect


def mensch_bei(plan: dict, t: float) -> tuple:
    """(x, y, blick_grad) des Menschen t Sekunden nach connect."""
    weg, tempo = plan["weg"], plan["tempo"]
    x, y = weg[0][0], weg[0][1]
    blick = 180.0
    t -= weg[0][2]
    if len(weg) > 1:
        blick = math.degrees(math.atan2(weg[1][1] - y, weg[1][0] - x))
    if t <= 0:
        return x, y, blick
    for (x1, y1, _), (x2, y2, pause) in zip(weg, weg[1:]):
        laenge = math.hypot(x2 - x1, y2 - y1)
        blick = math.degrees(math.atan2(y2 - y1, x2 - x1))
        dauer = laenge / tempo
        if t < dauer:
            a = t / dauer
            return x1 + a * (x2 - x1), y1 + a * (y2 - y1), blick
        t -= dauer + pause
        x, y = x2, y2
        if t < 0:
            return x, y, blick
    return x, y, blick


def mensch_einhaengen():
    import dataclasses

    from spotlab.backends import sim
    from spotlab.welt.raum import RaumTag

    cls = sim.SimBackend
    if getattr(cls.world_objects, "_kurs", False):
        return
    init_vorher, objekte_vorher = cls.__init__, cls.world_objects

    def __init__(self, *args, **kwargs):
        global MENSCH_T0
        MENSCH_T0 = UHR.v
        init_vorher(self, *args, **kwargs)

    def world_objects(self, kinds=None):
        raum = self._raum
        if not MENSCH or raum is None:
            return objekte_vorher(self, kinds)
        x, y, blick = mensch_bei(MENSCH, UHR.v - MENSCH_T0)
        # Der Tag hängt auf dem Rücken, schaut also entgegen der Gehrichtung.
        tag = RaumTag(id=MENSCH["tag"], x=x, y=y, grad=(blick + 180) % 360)
        self._raum = dataclasses.replace(raum, tags=tuple(raum.tags) + (tag,))
        try:
            return objekte_vorher(self, kinds)
        finally:
            self._raum = raum

    world_objects._kurs = True
    cls.__init__, cls.world_objects = __init__, world_objects


def _mensch_spur(plan: dict, dauer: float) -> list:
    """[[t, x, y, blick], ...] alle 0.2 s, dieselbe Zeitbasis wie der Weg."""
    spur, t = [], 0.0
    while t <= dauer + 0.2:
        x, y, b = mensch_bei(plan, t)
        spur.append([round(t, 2), round(x, 3), round(y, 3), round(b, 1)])
        t += 0.2
    return spur


def _bilder(ordner: Path, hoechstens: int = 8, max_bytes: int = 2_000_000) -> list:
    """PNG/JPG, die das Programm selbst gespeichert hat (nicht die Aufzeichnung unter runs/)."""
    import base64

    liste = []
    for pfad in sorted(ordner.rglob("*")):
        if "runs" in pfad.relative_to(ordner).parts or pfad.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            continue
        if len(liste) >= hoechstens:
            break
        daten = pfad.read_bytes()
        if len(daten) > max_bytes:
            liste.append({"name": pfad.name, "fehler": "zu gross zum Anzeigen"})
            continue
        art = "png" if pfad.suffix.lower() == ".png" else "jpeg"
        liste.append({"name": str(pfad.relative_to(ordner).as_posix()),
                      "daten": f"data:image/{art};base64," + base64.b64encode(daten).decode("ascii")})
    return liste


# Am echten Spot WARTEN lights() und beep() die Dauer ab (api/signals.py::_run,
# time.sleep(duration)); im Trockenlauf kehren sie sofort zurück. Ohne Ausgleich
# lägen im Kurs alle Signale auf demselben Zeitpunkt, und ein Programm, das am
# Gerät 5 s blinkt, wäre hier in null Sekunden vorbei (BEFUNDE_SPOTLAB.md, 4c).
# pose(): am Gerät wartet warte_auf, bis der Körper steht; wie lange das dauert,
# ist nicht gemessen. HALTUNG_S ist eine ANNAHME, dieselbe wie im Physikmodus von
# spotlab (1 s je Haltungsänderung, bis Abnahmepunkt A41).
HALTUNG_S = 1.0


def trockenlauf_wie_am_geraet():
    from spotlab.api import body, signals
    from spotlab.backends.dryrun import DryRunBackend

    if getattr(signals._run, "_kurs", False):
        return
    run_vorher, pose_vorher = signals._run, body.pose

    def _run(spot, art, behavior, duration, **daten):
        run_vorher(spot, art, behavior, duration, **daten)
        if spot.robot is None and isinstance(spot.backend, DryRunBackend):
            time.sleep(duration)

    def pose(spot, *args, **kwargs):
        pose_vorher(spot, *args, **kwargs)
        if isinstance(spot.backend, DryRunBackend):
            time.sleep(HALTUNG_S)

    _run._kurs = True
    signals._run = _run
    body.pose = pose


# Eigene Übungsräume des Kurses (z. B. «wohnung» für Kapitel 8) liegen neben diesem
# Modul in kursraeume/*.toml, im Format der spotlab-Vorlagen. spotlab selbst bleibt
# unverändert: nur die Suche nach dem Raum fragt zuerst hier.
KURSRAEUME = Path(__file__).resolve().parent / "kursraeume"


def kursraeume_einhaengen():
    from spotlab.welt import raum as raum_modul

    if getattr(raum_modul._pfad, "_kurs", False):
        return
    vorher = raum_modul._pfad

    def _pfad(name, workspace):
        eigen = KURSRAEUME / f"{name}.toml"
        return eigen if eigen.is_file() else vorher(name, workspace)

    _pfad._kurs = True
    raum_modul._pfad = _pfad


# ================================================================ Laufen

def lauf(code: str, raum: str = "leer", start: str = "", grenze_s: float = GRENZE_S) -> dict:
    """Führt `code` im Simulator aus und gibt zurück, was die Seite braucht."""
    installieren()
    ordner = Path(tempfile.mkdtemp(prefix="lauf-"))
    programm = ordner / "programm.py"
    programm.write_text(code, encoding="utf-8")

    # raum=trocken: der Trockenlauf von spotlab (echte Protobufs, nichts bewegt sich).
    # Er kann, was der 2D-Sim nicht kann: lights, beep, pose. Die Seite zeigt dann
    # statt der Karte eine Spot-Zeichnung, die die Signale abspielt.
    global AUFNAHME, MENSCH
    AUFNAHME = None
    MENSCH = None
    if raum and raum.startswith("kamera-"):
        szene = szenen()[raum]
        AUFNAHME = szene_lesen(raum)
        raum, start = szene["raum"], szene["start"]
    elif raum in MENSCHEN:
        MENSCH = MENSCHEN[raum]
        raum, start = MENSCH["raum"], start or MENSCH["start"]
    plan = MENSCH
    os.environ["SPOTLAB_BACKEND"] = "dryrun" if raum == "trocken" else "sim"
    if raum and raum not in ("keiner", "trocken"):
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
        AUFNAHME = None
        MENSCH = None
        _ABTASTER.clear()
        os.chdir(vorher_ordner)
        sys.argv = vorher_argv

    lauf_ordner = _lauf_ordner(ordner)
    ausgabe = puffer.getvalue()
    ereignisse = _jsonl(lauf_ordner / "ereignisse.jsonl") if lauf_ordner else []
    weg = _weg(lauf_ordner) if lauf_ordner else []
    angestossen = [e.get("daten", {}) for e in ereignisse if e.get("art") == "angestossen"]
    verweigert = [e.get("daten", {}) for e in ereignisse if e.get("art") == "treppe_verweigert"]
    if verweigert:
        # spotlab schreibt das nur in die Aufzeichnung; im Programm läuft walk() einfach
        # weiter, und Spot steht. Der Kurs sagt es dazu (wie die GUI im Protokoll).
        d = verweigert[0]
        ausgabe += (f"\n⚠ Spot ist bei x = {d.get('x', 0):.2f}, y = {d.get('y', 0):.2f} an der Treppe "
                     f"stehen geblieben: Hier geht es nur {d.get('verlangt', '?')} (Nase bergauf).\n")
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
        "signale": _signale(ereignisse),
        "bilder": _bilder(ordner),
        "treppe_verweigert": len(verweigert),
        "mensch": _mensch_spur(plan, max([p[0] for p in weg], default=0.0)) if plan else None,
        "dauer": round(UHR.v - beginn, 1),
    }


# Dieselben Namen wie spotlab.api.signals.COLORS (dort steht die Wahrheit).
FARBEN = {"blue": (0, 0, 255), "green": (0, 255, 0), "red": (255, 0, 0),
          "white": (255, 255, 255), "yellow": (255, 255, 0), "purple": (128, 0, 255)}
FARBEN_DEUTSCH = {"blue": "blau", "green": "grün", "red": "rot", "white": "weiss",
                  "yellow": "gelb", "purple": "violett"}


def farbname(rgb) -> str:
    for name, wert in FARBEN.items():
        if rgb is not None and tuple(rgb) == wert:
            return name
    return "rgb" + str(tuple(rgb)) if rgb is not None else "?"


SIGNALE = {
    "lights": ("color", "brightness", "duration"),
    "beep": ("note", "octave", "duration"),
    "pose": ("roll", "pitch", "yaw", "height"),
    "stand": (), "sit": (), "power_on": (), "power_off": (),
}


def _signale(ereignisse: list) -> list:
    """Licht, Ton, Haltung als Zeitstrahl für die Spot-Zeichnung: [{t, art, ...}]."""
    zeiten = [e["t"] for e in ereignisse if isinstance(e.get("t"), (int, float))]
    t0 = min(zeiten) if zeiten else 0.0
    liste = []
    for e in ereignisse:
        d = e.get("daten", {})
        if e.get("art") != "kommando" or d.get("name") not in SIGNALE:
            continue
        eintrag = {"t": round(e.get("t", t0) - t0, 2), "art": d["name"]}
        for feld in SIGNALE[d["name"]]:
            if feld in d:
                eintrag[feld] = d[feld]
        liste.append(eintrag)
    return liste


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
        elif art == "zurueck":
            text = f"Spot endet wieder an seinem Startplatz (± {w[0]:g} m)"
            if lage is None or len(weg) < 2:
                ok, detail = False, "Spot hat sich nicht bewegt."
            else:
                d = math.hypot(lage[1] - weg[0][1], lage[2] - weg[0][2])
                ok = d <= w[0] and any(math.hypot(p[1] - weg[0][1], p[2] - weg[0][2]) > 1.0 for p in weg)
                detail = (f"Er endet {d:.2f} m vom Start entfernt." if d > w[0]
                          else "" if ok else "Er war nie weiter als 1 m vom Start weg.")
        elif art == "treppe_richtig":
            n = e.get("treppe_verweigert", 0)
            text = "Spot nimmt die Treppe nur mit der Nase bergauf"
            ok, detail = n == 0, ("" if n == 0 else "An der Treppe ist er falsch herum stehen geblieben.")
        elif art in ("mensch_abstand", "mensch_nah"):
            spur = e.get("mensch") or []

            def abstand(p):
                if not spur:
                    return float("inf")
                m = spur[min(len(spur) - 1, max(0, round(p[0] / 0.2)))]
                return math.hypot(p[1] - m[1], p[2] - m[2])

            if art == "mensch_abstand":
                text = f"Spot kommt dem Menschen nie näher als {w[0]:g} m"
                if not weg:
                    ok, detail = False, "Kein Zustand aufgezeichnet."
                else:
                    am_naechsten = min(weg, key=abstand)
                    d = abstand(am_naechsten)
                    ok, detail = d >= w[0], f"Am nächsten war er {d:.2f} m (nach {am_naechsten[0]:.0f} s)."
            else:
                text = f"Am Ende ist Spot höchstens {w[0]:g} m vom Menschen entfernt"
                if lage is None:
                    ok, detail = False, "Spot hat sich nicht bewegt."
                else:
                    d = abstand(lage)
                    ok, detail = d <= w[0], f"Am Ende sind es {d:.2f} m."
        elif art == "licht":
            folge = [farbname(s.get("color")) for s in e.get("signale", []) if s["art"] == "lights"]
            text = "Spot leuchtet nacheinander: " + ", ".join(FARBEN_DEUTSCH.get(f, f) for f in w)
            ok = folge == list(w)
            detail = "Er leuchtet: " + (", ".join(FARBEN_DEUTSCH.get(f, f) for f in folge) or "gar nicht") + "."
        elif art == "toene":
            folge = [f"{s.get('note')}{s.get('octave')}" for s in e.get("signale", []) if s["art"] == "beep"]
            text = "Spot spielt nacheinander: " + " ".join(w)
            ok = folge == [t.upper() for t in w]
            detail = "Er spielt: " + (" ".join(folge) or "gar nichts") + "."
        elif art == "haltung":
            feld, soll = w
            werte = [s.get(feld, 0.0) for s in e.get("signale", []) if s["art"] == "pose"]
            einheit = " m" if feld == "height" else "°"
            text = f"Spot nimmt eine Haltung mit {feld} = {soll:g}{einheit} ein"
            ok = any(abs(v - soll) <= 0.5 for v in werte)
            detail = ("Er hat nie pose() bekommen." if not werte
                      else f"Seine Werte für {feld}: " + ", ".join(f"{v:g}" for v in werte) + ".")
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
    """Grundriss für die Karte. Eine Kamera-Szene zeigt ihren Raum mit Spot an der Aufnahmestelle."""
    kursraeume_einhaengen()
    from spotlab.welt.raum import raum_laden

    szene = szenen().get(name) or MENSCHEN.get(name)
    r = raum_laden(szene["raum"] if szene else name)
    start = [float(v) for v in szene["start"].split(",")] if szene else list(r.start)
    mensch = MENSCHEN.get(name)
    return {
        "name": r.name,
        "beschreibung": szene["titel"] if szene else r.beschreibung,
        "szene": bool(szene) and not mensch,
        "mensch": {"tag": mensch["tag"], "lage": list(mensch_bei(mensch, 0.0))} if mensch else None,
        "groesse": list(r.groesse) if r.groesse else None,
        "start": start,
        "waende": [[w.x1, w.y1, w.x2, w.y2] for w in r.waende],
        "bloecke": [{"name": b.name, "ecken": [list(p) for p in b.ecken()]} for b in r.bloecke],
        "boeden": [{"name": b.name, "art": b.art, "ecken": [list(p) for p in b.ecken()]} for b in r.boeden],
        "sperrzonen": [{"name": s.name, "ecken": [list(p) for p in s.ecken()]} for s in r.sperrzonen],
        "tags": [{"id": t.id, "x": t.x, "y": t.y, "grad": t.grad} for t in r.tags],
    }
