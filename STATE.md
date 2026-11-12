# Stand

**11.11.2026, Fassung 2: Python im Browser, live auf Vercel (Import durch den Autor).**
Repository: github.com/Lightrunnerwastaken/spotlab-learn (öffentlich).

Fertig:
- 12.11.2026: Durchsicht durch zwei Prüfer (als Schüler, alle Aufgaben selbst gelöst); bestätigte
  Funde korrigiert (2b502f8, live). Offen daraus: Kap. 9 Aufgabe 2 prüft supports() nicht (spotlab
  zeichnet es nicht auf); Python-Mittel wie getattr, f-String-Format, Listen-Schreibweise unerklärt.
- Alle 14 Kapitel geschrieben (… Einem Menschen folgen, Treppen und Kanten, Am
  echten Spot).
- Kapitel 13 (11.11. abends): Raum «treppe» von spotlab; `stairs()`, Nase bergauf
  (vorwärts hoch, rückwärts runter), Aufgabe hinauf/Tag 3/rückwärts runter von drei
  Starts (Ziel `treppe_richtig`: kein `treppe_verweigert` in der Aufzeichnung; der
  Kursmotor hängt dann eine ⚠-Zeile an die Ausgabe), Kante am Podest (look blocked,
  Spot bleibt stehen), `treppen = "auto"/"aus"`; A25 am Gerät offen, im Text gesagt.
- Kapitel 14 (11.11. abends): App-Auswahl (Übungsraum 3D, virtuell, Trockenlauf,
  Physik 3D, Echter Spot), Ablauf Übungsraum → Trockenlauf → Roboter, `supports()`,
  connect am Gerät (Anmelden, Uhr, Not-Aus, Lease), Aufräumen, «Kontrolle übernehmen»,
  Akku wechseln/Aufrichten, Läufe lesen über `spot.recorder.dir`, Gehzeit-Experiment,
  Projektideen. Nur Lesestoff und Quiz zu allem, was den echten Spot braucht.
- Die Seite kennt keine Tabellen und keine ```-Blöcke ohne Sprache: Formeln und
  Konfiguration als `| `-Zeilen, Listen statt Tabellen.
- Kapitel 12 (11.11. abends): `raum=mensch-<name>` = ein Mensch mit Tag 9 auf dem
  Rücken geht einen festen Weg (`kursmotor.MENSCHEN`, Tag wird bei jeder Abfrage an
  seine Stelle geschoben; spotlab unverändert). Die Seite zeichnet ihn mit (Ergebnis
  `mensch`). Inhalt: Finder/Regler, Drehregler (K = 0.3 bleibt unter der Drehschwelle
  hängen, K = 10 pendelt), Abstand halten (nie rückwärts), Wohnung: einfacher Regler
  verliert den Menschen an der Tür, Merkpunkt geradewegs stösst an, Aufgabe «Spur
  folgen» (drei Starts, Ziele `mensch_abstand`, `mensch_nah`); spotlabs `folgen.befehl`
  und `folgen.folge` laufen im Browser. Befund 4e.
- Kapitel 10 (11.11. abends): `raum=kamera-<szene>` = Spot steht im 2D-Raum, die Kameras
  liefern ImageResponse-Protobufs, die `tools/aufnahmen_bauen.py` vorher im 3D-Übungsraum
  (MuJoCo) aufgenommen hat (`motor/kursaufnahmen/*.bin.gz`, je 0.2 MB, im Zip). spotlabs
  Auswertung läuft unverändert darauf; Gehen ist in Szenen gesperrt. Bilder, die ein
  Programm als PNG/JPG speichert, zeigt die Seite unter der Ausgabe (`bilder`). Pillow
  lädt der Worker nur bei Bedarf. Neue Szene: Eintrag in SZENEN, Werkzeug laufen lassen.
- Kapitel 11: eigene Karte aus `blick.grid` beim Erkunden (Wohnung, 50 Schritte, alle
  Wände/Türen/Möbel), Wegpunktkette und Rückweg (Aufgabe, Ziel `zurueck`, drei Starts,
  im Browser 19 s), GraphNav am echten Spot als Lesecode (load_map, localize,
  navigate_to, Schleifenschluss).
- Kapitel 9 (11.11. abends): `raum=trocken` = spotlabs Trockenlauf; die Seite zeigt statt
  der Karte eine Bühne (Spot von der Seite/vorne/oben, LEDs, Töne per WebAudio, Ton-Knopf).
  Kursmotor liefert `signale` (Zeitstrahl), lights/beep warten wie am Gerät, pose 1 s
  (Annahme). Neue Ziele `licht`, `toene`, `haltung`. Aufgabe 2 läuft im 2D-Raum und
  verlangt dadurch `supports()`.
- Kapitel 8 (11.11. abends): Reflex bleibt stecken (Spot dreht sich vor der Kiste nur
  um), Gedächtnis mit Feldern 0.5 m + Dictionary + eigene Zahlenkarte, Tag 5 im
  Unbekannten finden, Aufgabe von drei Starts (30–45 Schritte), Projektideen.
  Eigener Kursraum «wohnung» in `motor/kursraeume/` (der Kursmotor sucht dort zuerst,
  spotlab bleibt unverändert). Im Browser: 3 Starts samt Abspielen 33 s.
- Kursmotor schneller: kein fsync, Zustand mit 5 Hz (Rechenzeit halbiert, Befund 4b).
- Kapitel 7 (11.11. abends): Tags lesen, Peilung → Ort im Raum, Suchen durch Gehen
  (Spot sieht rundum, bis 3 m, nur bei freier Sicht), Aufgabe «Vor dem Tag anhalten»
  im Raum «Möbliert» von vier Starts (einer muss erst suchen).
- Der Schülercode läuft im Browser: Pyodide 0.27.7 im Web Worker (`web/motor.js`),
  numpy/protobuf/wrapt aus Pyodide, bosdyn 5.0.1.2 von PyPI (nicht frei lizenziert,
  darum nicht im Repo), spotlab + `motor/kursmotor.py` aus `web/py/kurs-python.zip`.
- Kursmotor: virtuelle Uhr (Lauf von 70 s Spot-Zeit in ~3 s gerechnet), Abtaster ohne
  Thread, Attrappen für grpc/jwt/cryptography/urllib3/requests/keyring/pynmea2.
  Gegen den alten Echtzeit-Server verglichen: gleiche Wege, gleiche Zeiten.
- Aufgaben mit mehreren Startplätzen (`starts=`), Ziel `ende_in`, Hinweis beim Anstossen.
- `tests/kurs_pruefen.py` nimmt denselben Motor: 133 von 133 in Ordnung (16 s).
- Im Browser geprüft: Beispiel aus Kapitel 3, Türaufgabe aus Kapitel 6 (vier Starts,
  alle Ziele erfüllt). Erster Start lädt Python etwa 20 s, danach Sekunden.

Offen:
- GraphNav selbst ist im Kurs nicht
  ausführbar (nur am Gerät); Kamerabilder sind gerendert, nicht vom Gerät.
- Der Autor hat den Kurs noch nicht selbst durchgespielt.
