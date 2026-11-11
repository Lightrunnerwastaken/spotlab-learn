# Stand

**11.11.2026, Fassung 2: Python im Browser, live auf Vercel (Import durch den Autor).**
Repository: github.com/Lightrunnerwastaken/spotlab-learn (öffentlich).

Fertig:
- Kapitel 1–9 geschrieben (Einführung, Hallo Spot, Bewegen, Zustand, Umgebung,
  Hindernissen ausweichen, Objekte finden, Projekt: Unbekannter Raum, Licht/Ton/Haltung).
  Kapitel 10–14 als Vorschau (`bald: ja`).
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
- `tests/kurs_pruefen.py` nimmt denselben Motor: 81 von 81 in Ordnung (19 s).
- Im Browser geprüft: Beispiel aus Kapitel 3, Türaufgabe aus Kapitel 6 (vier Starts,
  alle Ziele erfüllt). Erster Start lädt Python etwa 20 s, danach Sekunden.

Offen:
- Kapitel 10–11 (Kameras, Karten) brauchen Fähigkeiten, die weder der 2D-Sim noch der
  Trockenlauf echt liefern (Befund 4); MuJoCo läuft im Browser nicht. Weg noch offen.
- Der Autor hat den Kurs noch nicht selbst durchgespielt.
