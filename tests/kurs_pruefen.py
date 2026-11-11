"""Prüft den ganzen Kurs mit dem Kursmotor — demselben Python, das im Browser läuft.

    python tests/kurs_pruefen.py            alles
    python tests/kurs_pruefen.py 06         nur Kapitel, deren Name mit 06 beginnt

- Jedes Codebeispiel läuft durch (oder endet mit Fehler, wenn `fehler=ja`).
- Jede Aufgabe: die Musterlösung in tests/loesungen/ besteht alle Ziele von
  JEDEM Startplatz aus; der Startcode besteht sie NICHT (sonst wäre sie geschenkt).
- Aussagen aus dem Kurstext und den Quizfragen werden nachgeprüft.

Mit dem Python ausführen, in dem spotlab installiert ist. Der Motor läuft mit
virtueller Uhr, ein Lauf dauert deshalb Sekunden statt Minuten.
"""

from __future__ import annotations

import multiprocessing
import sys
import time
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "motor"))

import kursparser  # noqa: E402

LOESUNGEN = Path(__file__).parent / "loesungen"
PROZESSE = 6

KOPF = "from spotlab import connect\nwith connect() as spot:\n    spot.power_on(); spot.stand()\n"

# Die Erkundung mit Gedächtnis aus Kapitel 8, Platzhalter SCHRITTE und STOPP (Code vor
# jedem Schritt, eingerückt mit 8 Leerzeichen).
ERKUNDEN = (
    "import math\n"
    "def feld(x, y):\n    return (int(x // 0.5), int(y // 0.5))\n"
    "besuche = {}\nmax_y = 0\n" + KOPF +
    "    for schritt in range(SCHRITTE):\n"
    "STOPP"
    "        z = spot.state\n        max_y = max(max_y, z.y)\n"
    "        besuche[feld(z.x, z.y)] = besuche.get(feld(z.x, z.y), 0) + 1\n"
    "        blick = spot.look(max_distance=1.0, start=0.6, margin=0.35)\n"
    "        bw, bz = None, None\n"
    "        for w in sorted(range(-180, 180, 15), key=abs):\n"
    "            if blick.direction(w).status != 'clear':\n                continue\n"
    "            r = math.radians(z.heading + w)\n"
    "            n = besuche.get(feld(z.x + math.cos(r), z.y + math.sin(r)), 0)\n"
    "            if bz is None or n < bz:\n                bw, bz = w, n\n"
    "        if bw is None:\n            spot.move(turn=90)\n"
    "        else:\n            spot.move(turn=bw); spot.move(forward=0.5)\n"
)

# Aussagen aus dem Text: (Kapitel, Beschreibung, Raum, Start, Code, erwarteter Status oder "*",
#                         Text in der Ausgabe, muss anstossen)
BEHAUPTUNGEN = [
    ("02", "Quiz: Befehl nach dem with-Block scheitert", "leer", "",
     "from spotlab import connect\nwith connect() as spot:\n    spot.power_on()\nspot.stand()\n",
     "fehler", "", False),
    ("03", "Quiz: Weg endet bei (2, 2)", "leer", "",
     KOPF + "    spot.move(forward=2); spot.move(turn=90); spot.move(forward=1)\n"
     "    spot.move(turn=90); spot.move(forward=1)\n"
     "    z = spot.state\n    print('ENDE', round(z.x), round(z.y))\n",
     "fertig", "ENDE 2 2", False),
    ("03", "walk 0.5 m/s während 2 s kommt weniger als 1 m weit", "moebliert", "",
     KOPF + "    spot.walk(vx=0.5, duration=2)\n    print('KURZ', spot.state.x - 1.0 < 0.95)\n",
     "fertig", "KURZ True", False),
    ("05", "Quiz: Schritte von 1.5 m stossen an die Wand", "leer", "0.5,2.5,0",
     KOPF + "    while spot.look(max_distance=1.0, start=0.6).front.status == 'clear':\n"
     "        spot.move(forward=1.5)\n",
     "*", "", True),
    ("05", "look() ohne start ist überall unbekannt", "moebliert", "",
     KOPF + "    b = spot.look()\n"
     "    print('ALLE', all(getattr(b, r).status == 'unknown' for r in ('front','left','right','back')))\n",
     "fertig", "ALLE True", False),
    ("06", "Ausweichen: vorne und links zu, rechts frei", "durchgang", "1,3.2,0",
     KOPF + "    b = spot.look(start=0.6)\n    print('ST', b.front.status, b.left.status, b.right.status)\n",
     "fertig", "ST blocked blocked clear", False),
    ("06", "Halbkreis: bei -90° (Tür) ist frei", "durchgang", "3,2,90",
     KOPF + "    print('TUER', spot.look(max_distance=1.8, start=0.6).direction(-90).status)\n",
     "fertig", "TUER clear", False),
    ("06", "Kistenecke: mit margin 0.3 ist vorne frei", "durchgang", "1.68,2.63,-15",
     KOPF + "    print('M3', spot.look(max_distance=1.2, start=0.6, margin=0.3).front.status)\n",
     "fertig", "M3 clear", False),
    ("06", "Kistenecke: mit margin 0.35 ist vorne zu", "durchgang", "1.68,2.63,-15",
     KOPF + "    print('M35', spot.look(max_distance=1.2, start=0.6, margin=0.35).front.status)\n",
     "fertig", "M35 blocked", False),
    ("07", "Quiz: in der Mitte ist Tag 2 der nächste", "moebliert", "3.5,2.7,0",
     KOPF + "    print('IDS', [t.id for t in spot.tags()])\n",
     "fertig", "IDS [2, 1]", False),
    ("07", "Nach Drehen um die Peilung liegt der Tag vorne", "moebliert", "3.5,2.7,0",
     KOPF + "    spot.move(turn=spot.tags(id=1)[0].bearing)\n"
     "    print('VORNE', abs(spot.tags(id=1)[0].bearing) < 2)\n",
     "fertig", "VORNE True", False),
    ("07", "Aus Peilung und Abstand: Tag 1 bei (5.9, 2)", "moebliert", "3.5,2.7,0",
     "import math\n" + KOPF + "    z = spot.state; t = spot.tags(id=1)[0]\n"
     "    r = math.radians(z.heading + t.bearing)\n"
     "    print('ORT', round(z.x + t.distance * math.cos(r), 1), round(z.y + t.distance * math.sin(r), 1))\n",
     "fertig", "ORT 5.9 2.0", False),
    ("07", "Direkt hingehen: Spot stösst an die WAND (nicht an den Tisch)", "moebliert", "3.5,2.7,0",
     KOPF + "    t = spot.tags(id=1)[0]; spot.move(turn=t.bearing)\n"
     "    try:\n        spot.move(forward=t.distance)\n    except Exception:\n        pass\n"
     "    print('WAND', spot.state.x > 5.4)\n",
     "fertig", "WAND True", True),
    ("07", "Aus der Ecke sieht Spot in keiner Richtung einen Tag", "moebliert", "1,1,0",
     KOPF + "    n = 0\n    for i in range(8):\n        n += len(spot.tags()); spot.move(turn=45)\n"
     "    print('KEINE', n == 0)\n",
     "fertig", "KEINE True", False),
    ("07", "Quiz: ein Hindernis nimmt die Sicht auf einen nahen Tag", "moebliert", "0.5,2.6,0",
     KOPF + "    print('VERDECKT', spot.tags(id=2) == [])\n",
     "fertig", "VERDECKT True", False),
    ("07", "Quiz: am Hindernis vorbei ist die Sicht frei", "moebliert", "2.3,2.6,0",
     KOPF + "    print('FREI', [t.id for t in spot.tags(id=2)])\n",
     "fertig", "FREI [2]", False),
    ("08", "Reflex: Spot kommt in 12 Schritten nicht vom Fleck", "wohnung", "4,1.2,0",
     KOPF + "    for i in range(12):\n"
     "        b = spot.look(max_distance=1.0, start=0.6, margin=0.35)\n"
     "        if b.front.status == 'clear': spot.move(forward=0.5)\n"
     "        elif b.left.status == 'clear': spot.move(turn=90)\n"
     "        elif b.right.status == 'clear': spot.move(turn=-90)\n"
     "        else: spot.move(turn=180)\n"
     "    z = spot.state\n    print('FLECK', abs(z.x - 4) < 0.05 and abs(z.y - 1.2) < 0.05)\n",
     "fertig", "FLECK True", False),
    ("08", "Gedächtnis: aus derselben Ecke ins obere Zimmer", "wohnung", "4,1.2,0",
     ERKUNDEN.replace("SCHRITTE", "30").replace("STOPP", "") + "    print('OBEN', max_y > 2.8)\n",
     "fertig", "OBEN True", False),
    ("08", "Suche ab (1, 1): sieht Tag 5 vom oberen Zimmer aus durch die Tür", "wohnung", "1,1,90",
     ERKUNDEN.replace("SCHRITTE", "80").replace(
         "STOPP", "        if spot.tags(id=5):\n            break\n")
     + "    z = spot.state\n    print('DURCH', z.y > 2.6, len(spot.tags(id=5)))\n",
     "fertig", "DURCH True 1", False),
    ("09", "Quiz: lights wartet die Dauer ab, erst dann geht move", "trocken", "",
     "import time\n" + KOPF + "    a = time.time(); spot.lights('red', duration=3)\n"
     "    print('WARTET', round(time.time() - a, 1))\n",
     "fertig", "WARTET 3.0", False),
    ("09", "Quiz: beep('H') ist ein ValueError", "trocken", "",
     KOPF + "    spot.beep('H')\n", "fehler", "ValueError: note muss C, D, E, F, G, A oder B sein", False),
    ("09", "2D-Übungsraum: kein Licht, Ton, pose; look und tags ja", "leer", "",
     "from spotlab import connect\nwith connect() as spot:\n"
     "    print('KANN', [spot.supports(f) for f in ['lights', 'beep', 'pose', 'look', 'tags', 'camera']])\n",
     "fertig", "KANN [False, False, False, True, True, False]", False),
    ("09", "Trockenlauf kann Licht, Ton und pose", "trocken", "",
     "from spotlab import connect\nwith connect() as spot:\n"
     "    print('KANN', [spot.supports(f) for f in ['lights', 'beep', 'pose']])\n",
     "fertig", "KANN [True, True, True]", False),
    ("09", "Das universelle Programm (Aufgabe 2) läuft auch im Trockenlauf durch", "trocken", "",
     (WURZEL / "tests" / "loesungen" / "09-licht-ton-haltung-3-9.py").read_text(encoding="utf-8"),
     "fertig", "Begrüssung fertig", False),
] + [
    ("08", f"Aufgabe: von {s} aus ist Tag 5 nicht sofort zu sehen", "wohnung", s,
     KOPF + "    print('ANFANG', len(spot.tags(id=5)))\n",
     "fertig", "ANFANG 0", False)
    for s in ("1,1,90", "7,4,180", "1,4.5,-90")
]


def _arbeiter(auftrag):
    import kursmotor
    code, raum, start, ziele = auftrag
    return kursmotor.lauf_mit_pruefung(code, raum, start, ziele)


def _alle_ok(e):
    pr = e.get("pruefung") or []
    ok = bool(pr) and all(p["ok"] for p in pr)
    return ok, "; ".join(f"{p['text']}: {p['detail']}" for p in pr if not p["ok"]) or "keine Prüfung"


def auftraege_sammeln(filter_):
    """[(Name, [(code, raum, start, ziele), ...], Prüfung über die Liste der Ergebnisse)]"""
    kurs = kursparser.kurs_lesen()
    liste = []
    for k in kurs["kapitel"]:
        if filter_ and not k["id"].startswith(filter_):
            continue
        for ai, a in enumerate(k["abschnitte"]):
            for bi, b in enumerate(a["bloecke"]):
                wo = f"{k['id']}/{ai}/{bi}"
                if b["art"] == "code":
                    soll = "fehler" if b["fehler_erwartet"] else "fertig"
                    liste.append((f"Beispiel {wo} ({a['titel']})", [(b["code"], b["raum"], b["start"], None)],
                                  lambda es, soll=soll: (es[0]["status"] == soll,
                                                         f"Status {es[0]['status']}, erwartet {soll}: {es[0]['ausgabe'][-300:]!r}")))
                elif b["art"] == "aufgabe":
                    datei = LOESUNGEN / f"{k['id']}-{ai}-{bi}.py"
                    if not datei.exists():
                        liste.append((f"Aufgabe {wo}", [], lambda es, d=datei: (False, f"Musterlösung fehlt: {d.name}")))
                        continue
                    loesung = datei.read_text(encoding="utf-8")

                    def alle(es):
                        schlecht = [(i, _alle_ok(e)[1]) for i, e in enumerate(es) if not _alle_ok(e)[0]]
                        return not schlecht, " | ".join(f"Start {i + 1}: {w}" for i, w in schlecht)

                    def nicht_alle(es):
                        return not all(_alle_ok(e)[0] for e in es), "Startcode besteht schon alles"

                    liste.append((f"Aufgabe {wo} Musterlösung ({len(b['starts'])} Starts)",
                                  [(loesung, b["raum"], s, b["ziele"]) for s in b["starts"]], alle))
                    liste.append((f"Aufgabe {wo} Startcode",
                                  [(b["code"], b["raum"], s, b["ziele"]) for s in b["starts"]], nicht_alle))
    for kap, name, raum, start, code, soll, text, stoss in BEHAUPTUNGEN:
        if filter_ and not kap.startswith(filter_):
            continue

        def pruefung(es, soll=soll, text=text, stoss=stoss):
            e = es[0]
            if stoss:
                ok = bool(e["angestossen"])
            else:
                ok = (soll == "*" or e["status"] == soll) and text in e["ausgabe"]
            return ok, f"Status {e['status']}; Ausgabe: {e['ausgabe'][-200:]!r}"
        liste.append((f"Kap. {kap}: {name}", [(code, raum, start, None)], pruefung))
    return liste


def main():
    filter_ = sys.argv[1] if len(sys.argv) > 1 else ""
    auftraege = auftraege_sammeln(filter_)
    flach = [spec for _, specs, _ in auftraege for spec in specs]
    print(f"{len(auftraege)} Prüfungen, {len(flach)} Läufe, {PROZESSE} Prozesse ...")
    beginn = time.time()
    with multiprocessing.Pool(PROZESSE) as pool:
        ergebnisse = pool.map(_arbeiter, flach, chunksize=1)

    fehler, i = 0, 0
    for name, specs, pruefung in auftraege:
        teil = ergebnisse[i:i + len(specs)]
        i += len(specs)
        ok, warum = pruefung(teil)
        print(("OK    " if ok else "FALSCH"), name, "" if ok else f"-> {warum}")
        fehler += not ok
    print(f"\n{len(auftraege) - fehler} von {len(auftraege)} in Ordnung ({time.time() - beginn:.0f} s)")
    sys.exit(1 if fehler else 0)


if __name__ == "__main__":
    main()
