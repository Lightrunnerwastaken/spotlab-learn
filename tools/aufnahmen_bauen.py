"""Nimmt die Kamera-Szenen für Kapitel 10 im 3D-Übungsraum von spotlab auf.

    python tools/aufnahmen_bauen.py

Braucht spotlab mit dem MuJoCo-Übungsraum (Extra [sim]) — das läuft NICHT im
Browser. Darum wird hier einmal aufgenommen: Spot steht in einem Raum von spotlab
an einer festen Stelle, und für jede Kamera werden die Antworten gespeichert, die
`backend.images()` liefert (echte `ImageResponse`-Protobufs mit Bild, Tiefe,
Kalibrierung und Rahmenbaum). Im Browser gibt der Kursmotor genau diese Antworten
zurück (`kursmotor.kamera_einhaengen`), und spotlabs eigene Auswertung
(`Image`, `DepthImage`, `point_cloud`) läuft unverändert darauf.

Ergebnis: motor/kursaufnahmen/<szene>.bin.gz (gzip) und szenen.json. `baue.py`
legt sie nach web/py/aufnahmen/; der Browser holt sie erst, wenn eine Szene läuft. Die Bilder sind
GERENDERT (MuJoCo), nicht vom echten Spot — der Kurs sagt das.
"""

from __future__ import annotations

import gzip
import json
import os
import struct
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
ZIEL = WURZEL / "motor" / "kursaufnahmen"

SZENEN = {
    "kamera-tisch": {"raum": "moebliert", "start": "1.2,1.8,0",
                     "titel": "Spot steht im Raum «Möbliert» vor dem Tisch"},
    "kamera-tuer": {"raum": "durchgang", "start": "3.4,2.0,0",
                    "titel": "Spot steht im Raum «Durchgang» vor der Tür"},
}


def schreiben(pfad: Path, antworten: dict[str, bytes]) -> None:
    """Einfaches Format: je Quelle Länge+Name, Länge+Protobuf (Little Endian)."""
    with gzip.open(pfad, "wb", compresslevel=9) as f:
        for name, daten in antworten.items():
            n = name.encode("utf-8")
            f.write(struct.pack("<I", len(n)) + n + struct.pack("<I", len(daten)) + daten)


def lesen(pfad: Path) -> dict[str, bytes]:
    daten, i, aus = gzip.decompress(pfad.read_bytes()), 0, {}
    while i < len(daten):
        (n,) = struct.unpack_from("<I", daten, i); i += 4
        name = daten[i:i + n].decode("utf-8"); i += n
        (m,) = struct.unpack_from("<I", daten, i); i += 4
        aus[name] = daten[i:i + m]; i += m
    return aus


def aufnehmen(szene: str, angabe: dict) -> dict[str, bytes]:
    import spotlab

    os.environ["SPOTLAB_RAUM_START"] = angabe["start"]
    with spotlab.connect(backend="mujoco", raum=angabe["raum"]) as spot:
        spot.power_on()
        spot.stand()
        quellen = spot.backend.image_sources()
        antworten = spot.backend.images(quellen)
        z = spot.state
        print(f"{szene}: Spot bei x={z.x:.2f} y={z.y:.2f} Blick {z.heading:.0f}°, "
              f"{len(quellen)} Quellen")
        return {q: a.SerializeToString() for q, a in zip(quellen, antworten)}


def main():
    os.environ["SPOTLAB_NUR_TROCKEN"] = "1"
    ZIEL.mkdir(parents=True, exist_ok=True)
    namen = sys.argv[1:] or list(SZENEN)
    for szene in namen:
        antworten = aufnehmen(szene, SZENEN[szene])
        pfad = ZIEL / f"{szene}.bin.gz"
        schreiben(pfad, antworten)
        print(f"  {pfad.name}: {pfad.stat().st_size / 1e6:.2f} MB")
    (ZIEL / "szenen.json").write_text(
        json.dumps(SZENEN, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
