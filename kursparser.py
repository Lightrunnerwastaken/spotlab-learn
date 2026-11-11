"""Liest die Kapitel aus kurs/*.md in eine Form, die die Webseite anzeigt.

Ein Kapitel ist eine Textdatei. Oben steht ein Kopf zwischen zwei `---`-Zeilen
(nummer, titel, optional `bald: ja` für ein Kapitel, das noch nicht geschrieben
ist, und `abschnitte:` als Liste für dessen Vorschau). Jede Überschrift `# ...`
beginnt einen Abschnitt, also eine Seite mit „Zurück" und „Weiter".

Innerhalb eines Abschnitts gibt es vier Arten von Blöcken:

    Text            gewöhnliche Absätze, **fett**, `Code`, Listen mit "- ",
                    Zwischentitel mit "## ", Hinweise mit "> "
    ```spot raum=moebliert start=1,1,0
    ...Code...      ein Codefeld zum Ausführen im Simulator
    ```             (raum=keiner: ohne Karte; fehler=ja: endet absichtlich mit Fehler)
    ```quiz punkte=1
    ? Frage
    A) falsch
    B)* richtig      (* markiert die richtige Antwort)
    ! Erklärung, die nach dem Lösen erscheint
    ```
    ```aufgabe raum=moebliert punkte=2 starts=1,3,0;1,1,0
    (starts: das Programm muss von JEDEM dieser Plätze aus bestehen)
    ziel: ende_bei 3.0 2.0 0.4     (x, y, Toleranz in m)
    ziel: ende_in 5 0 9 4          (Rechteck x1 y1 x2 y2)
    ziel: blick 90 15              (Grad, Toleranz in Grad)
    ziel: nicht_angestossen
    ziel: ausgabe 42               (Text muss in der Ausgabe stehen)
    ziel: aufgerufen move          (Kommando muss vorkommen)
    ziel: gefahren 1.0             (mindestens so viele Meter Weg)
    ziel: licht blue green         (genau diese Farben nacheinander, raum=trocken)
    ziel: toene C5 E5 G5           (genau diese Töne nacheinander)
    ziel: haltung pitch 15         (ein pose() mit diesem Wert, ± 0.5)
    ziel: zurueck 0.3              (endet so nah am EIGENEN Startplatz, geht mit starts=)
    tipp: ein Tipp, der nach dem ersten Fehlversuch erscheint
    ---
    ...Startcode...
    ```
"""

from __future__ import annotations

import re
from pathlib import Path

KURS = Path(__file__).parent / "kurs"

ZIELARTEN = {
    "ende_bei": 3,
    "ende_in": 4,         # x1 y1 x2 y2: Spot endet in diesem Rechteck
    "blick": 2,
    "nicht_angestossen": 0,
    "ausgabe": None,      # Rest der Zeile ist der Text
    "aufgerufen": 1,
    "gefahren": 1,
    "steht": 0,
    "sitzt": 0,
    "licht": "liste",     # Farben in dieser Reihenfolge: licht blue green
    "toene": "liste",     # Töne in dieser Reihenfolge: toene C5 E5 G5
    "haltung": 2,         # irgendein pose() mit diesem Wert: haltung pitch 15
    "zurueck": 1,         # endet höchstens so weit (m) vom eigenen Startplatz
    "mensch_abstand": 1,  # raum=mensch-*: nie näher als so viele Meter am Menschen
    "mensch_nah": 1,      # raum=mensch-*: am Ende höchstens so weit vom Menschen
    "treppe_richtig": 0,  # spotlab hat keine Treppe falsch herum verweigert
}


class KursFehler(ValueError):
    pass


def _optionen(kopf: str) -> dict:
    """`raum=moebliert punkte=2` -> {"raum": "moebliert", "punkte": "2"}"""
    return dict(re.findall(r"(\w+)=(\S+)", kopf))


def _kopf_lesen(zeilen: list[str], datei: str) -> tuple[dict, list[str]]:
    if not zeilen or zeilen[0].strip() != "---":
        raise KursFehler(f"{datei}: der Kopf (---) fehlt in Zeile 1")
    kopf, liste = {}, None
    for i, zeile in enumerate(zeilen[1:], start=1):
        if zeile.strip() == "---":
            return kopf, zeilen[i + 1:]
        if zeile.startswith("  - ") and liste is not None:
            kopf[liste].append(zeile[4:].strip())
            continue
        name, _, wert = zeile.partition(":")
        name, wert = name.strip(), wert.strip()
        if not wert:
            kopf[name], liste = [], name
        else:
            kopf[name], liste = wert, None
    raise KursFehler(f"{datei}: der Kopf wird nie mit --- geschlossen")


def _quiz(inhalt: list[str], opt: dict, wo: str) -> dict:
    frage, antworten, erklaerung = [], [], []
    for zeile in inhalt:
        m = re.match(r"^([A-H])\)(\*?)\s*(.*)$", zeile)
        if zeile.startswith("|") and not antworten:
            frage.append(zeile.rstrip())          # Codezeile, Einrückung behalten
        elif zeile.startswith("?"):
            frage.append(zeile[1:].strip())
        elif m:
            antworten.append({"text": m.group(3), "richtig": bool(m.group(2))})
        elif zeile.startswith("!"):
            erklaerung.append(zeile[1:].strip())
        elif zeile.strip() and antworten:
            antworten[-1]["text"] += " " + zeile.strip()
        elif zeile.strip():
            frage.append(zeile.strip())
    if not frage or len(antworten) < 2:
        raise KursFehler(f"{wo}: ein Quiz braucht eine Frage (?) und mindestens zwei Antworten")
    if sum(a["richtig"] for a in antworten) != 1:
        raise KursFehler(f"{wo}: genau eine Antwort muss mit * als richtig markiert sein")
    return {
        "art": "quiz",
        "frage": "\n".join(frage),
        "antworten": antworten,
        "erklaerung": "\n".join(erklaerung),
        "punkte": int(opt.get("punkte", 1)),
    }


def _ziel(text: str, wo: str) -> dict:
    teile = text.split(None, 1)
    art = teile[0]
    rest = teile[1] if len(teile) > 1 else ""
    if art not in ZIELARTEN:
        raise KursFehler(f"{wo}: unbekanntes Ziel '{art}' (bekannt: {', '.join(ZIELARTEN)})")
    anzahl = ZIELARTEN[art]
    if anzahl is None:
        return {"art": art, "werte": [rest.strip().strip('"')]}
    werte = rest.split()
    if anzahl == "liste":
        if not werte:
            raise KursFehler(f"{wo}: Ziel '{art}' braucht mindestens einen Wert")
        return {"art": art, "werte": werte}
    if len(werte) != anzahl:
        raise KursFehler(f"{wo}: Ziel '{art}' braucht {anzahl} Werte, hat {len(werte)}")
    if art == "haltung":
        if werte[0] not in ("roll", "pitch", "yaw", "height"):
            raise KursFehler(f"{wo}: haltung kennt roll, pitch, yaw, height, nicht '{werte[0]}'")
        werte = [werte[0], float(werte[1])]
    elif art != "aufgerufen":
        werte = [float(w) for w in werte]
    return {"art": art, "werte": werte}


def _aufgabe(inhalt: list[str], opt: dict, wo: str) -> dict:
    if "---" not in [z.strip() for z in inhalt]:
        raise KursFehler(f"{wo}: eine Aufgabe braucht eine Zeile --- vor dem Startcode")
    trenner = [z.strip() for z in inhalt].index("---")
    ziele, tipps = [], []
    for zeile in inhalt[:trenner]:
        if zeile.startswith("ziel:"):
            ziele.append(_ziel(zeile[5:].strip(), wo))
        elif zeile.startswith("tipp:"):
            tipps.append(zeile[5:].strip())
        elif zeile.strip():
            raise KursFehler(f"{wo}: unbekannte Zeile in der Aufgabe: {zeile!r}")
    if not ziele:
        raise KursFehler(f"{wo}: eine Aufgabe braucht mindestens ein Ziel")
    starts = [s for s in opt.get("starts", "").split(";") if s] or [opt.get("start", "")]
    return {
        "art": "aufgabe",
        "raum": opt.get("raum", "leer"),
        "start": starts[0],
        "starts": starts,
        "punkte": int(opt.get("punkte", 2)),
        "ziele": ziele,
        "tipps": tipps,
        "code": "\n".join(inhalt[trenner + 1:]).strip("\n") + "\n",
    }


def _bloecke(zeilen: list[str], wo: str) -> list[dict]:
    bloecke, text = [], []

    def text_abschliessen():
        roh = "\n".join(text).strip("\n")
        if roh.strip():
            bloecke.append({"art": "text", "text": roh})
        text.clear()

    i = 0
    while i < len(zeilen):
        zeile = zeilen[i]
        m = re.match(r"^```(\w+)\s*(.*)$", zeile)
        if m and m.group(1) in ("spot", "python", "quiz", "aufgabe"):
            text_abschliessen()
            art, opt = m.group(1), _optionen(m.group(2))
            inhalt = []
            i += 1
            while i < len(zeilen) and zeilen[i].rstrip() != "```":
                inhalt.append(zeilen[i])
                i += 1
            if i >= len(zeilen):
                raise KursFehler(f"{wo}: ein ```{art}-Block wird nie geschlossen")
            if art == "spot":
                bloecke.append({
                    "art": "code",
                    "raum": opt.get("raum", "leer"),
                    "start": opt.get("start", ""),
                    # für die Tests: dieses Beispiel soll absichtlich mit einem Fehler enden
                    "fehler_erwartet": opt.get("fehler") == "ja",
                    "code": "\n".join(inhalt).strip("\n") + "\n",
                })
            elif art == "python":
                # nur zum Lesen, ohne Ausführen
                bloecke.append({"art": "zeigen", "code": "\n".join(inhalt).strip("\n")})
            elif art == "quiz":
                bloecke.append(_quiz(inhalt, opt, wo))
            else:
                bloecke.append(_aufgabe(inhalt, opt, wo))
        else:
            text.append(zeile)
        i += 1
    text_abschliessen()
    return bloecke


def kapitel_lesen(pfad: Path) -> dict:
    zeilen = pfad.read_text(encoding="utf-8").splitlines()
    kopf, rest = _kopf_lesen(zeilen, pfad.name)
    for feld in ("nummer", "titel"):
        if feld not in kopf:
            raise KursFehler(f"{pfad.name}: im Kopf fehlt '{feld}'")
    kapitel = {
        "id": pfad.stem,
        "nummer": int(kopf["nummer"]),
        "titel": kopf["titel"],
        "bald": kopf.get("bald", "nein") == "ja",
        "abschnitte": [],
    }
    if kapitel["bald"]:
        kapitel["abschnitte"] = [{"titel": t, "bloecke": []} for t in kopf.get("abschnitte", [])]
        return kapitel

    titel, sammlung = None, []

    def abschliessen():
        if titel is None:
            if any(z.strip() for z in sammlung):
                raise KursFehler(f"{pfad.name}: Text vor der ersten Überschrift '# ...'")
            return
        wo = f"{pfad.name}, Abschnitt '{titel}'"
        kapitel["abschnitte"].append({"titel": titel, "bloecke": _bloecke(sammlung, wo)})

    imcode = False
    for zeile in rest:
        if zeile.startswith("```"):
            if not imcode:
                imcode = True
            elif zeile.rstrip() == "```":
                imcode = False
        if not imcode and zeile.startswith("# "):
            abschliessen()
            titel, sammlung = zeile[2:].strip(), []
        else:
            sammlung.append(zeile)
    abschliessen()
    if not kapitel["abschnitte"]:
        raise KursFehler(f"{pfad.name}: kein Abschnitt (Überschrift '# ...') gefunden")
    return kapitel


def kurs_lesen(ordner: Path = KURS) -> dict:
    kapitel = [kapitel_lesen(p) for p in sorted(ordner.glob("*.md"))]
    kapitel.sort(key=lambda k: k["nummer"])
    return {"titel": "Spot programmieren", "kapitel": kapitel}


def aufgabe_finden(kurs: dict, schluessel: str) -> dict | None:
    """`02-hallo-spot/1/0` -> der Aufgabenblock (Kapitel/Abschnitt/Block)."""
    try:
        kid, a, b = schluessel.split("/")
        for k in kurs["kapitel"]:
            if k["id"] == kid:
                block = k["abschnitte"][int(a)]["bloecke"][int(b)]
                return block if block["art"] == "aufgabe" else None
    except (ValueError, IndexError, KeyError):
        return None
    return None
