"""Baut alles, was die Webseite ohne Server braucht, in den Ordner web/.

    python baue.py

Erzeugt:
    web/kurs.json               alle Kapitel aus kurs/*.md
    web/raeume/<name>.json      die Übungsräume von spotlab als Grundriss
    web/py/kurs-python.zip      spotlab (ohne GUI) und der Kursmotor für Pyodide

Mit dem Python ausführen, in dem spotlab installiert ist. Die erzeugten Dateien
gehören ins Repository: Vercel liefert web/ nur aus und baut nichts.

bosdyn (Boston Dynamics) steht NICHT im Zip: es ist nicht frei lizenziert. Der
Browser holt es beim ersten Start selbst von PyPI, wie pip es täte.
"""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

WURZEL = Path(__file__).parent
WEB = WURZEL / "web"
sys.path.insert(0, str(WURZEL / "motor"))

import kursparser  # noqa: E402

AUSLASSEN = {"gui", "mcp", "editor", "__pycache__"}
NUR_ENDUNGEN = {".py", ".toml", ".json", ".txt", ".md"}


def kurs_bauen() -> dict:
    kurs = kursparser.kurs_lesen()
    (WEB / "kurs.json").write_text(json.dumps(kurs, ensure_ascii=False, separators=(",", ":")),
                                   encoding="utf-8")
    return kurs


def raeume_bauen(kurs: dict) -> list[str]:
    import kursmotor
    from spotlab.welt.raum import vorlagen

    namen = set()
    for vorlage in vorlagen():
        namen.add(Path(str(vorlage)).stem if not isinstance(vorlage, str) else vorlage)
    for k in kurs["kapitel"]:
        for a in k["abschnitte"]:
            for b in a["bloecke"]:
                if b.get("raum") and b["raum"] != "keiner":
                    namen.add(b["raum"])
    ziel = WEB / "raeume"
    ziel.mkdir(exist_ok=True)
    for name in sorted(namen):
        (ziel / f"{name}.json").write_text(
            json.dumps(kursmotor.raum_als_json(name), ensure_ascii=False), encoding="utf-8")
    return sorted(namen)


def python_bauen() -> tuple[int, str]:
    import spotlab

    quelle = Path(spotlab.__file__).parent
    try:
        stand = subprocess.run(["git", "-C", str(quelle), "describe", "--always", "--dirty"],
                               capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        stand = "unbekannt"
    ziel = WEB / "py"
    ziel.mkdir(exist_ok=True)
    zip_pfad = ziel / "kurs-python.zip"
    anzahl = 0
    with zipfile.ZipFile(zip_pfad, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for datei in sorted(quelle.rglob("*")):
            teile = datei.relative_to(quelle).parts
            if not datei.is_file() or AUSLASSEN & set(teile) or datei.suffix not in NUR_ENDUNGEN:
                continue
            z.write(datei, Path("spotlab", *teile).as_posix())
            anzahl += 1
        z.write(WURZEL / "motor" / "kursmotor.py", "kursmotor.py")
        for raum in sorted((WURZEL / "motor" / "kursraeume").glob("*.toml")):
            z.write(raum, f"kursraeume/{raum.name}")
        z.writestr("spotlab_stand.txt", f"spotlab {spotlab.__version__} ({stand})\n")
    return anzahl, f"spotlab {spotlab.__version__} ({stand}), {zip_pfad.stat().st_size / 1e6:.2f} MB"


def main():
    kurs = kurs_bauen()
    raeume = raeume_bauen(kurs)
    anzahl, stand = python_bauen()
    print(f"kurs.json: {len(kurs['kapitel'])} Kapitel")
    print(f"raeume: {', '.join(raeume)}")
    print(f"kurs-python.zip: {anzahl} Dateien, {stand}")


if __name__ == "__main__":
    main()
