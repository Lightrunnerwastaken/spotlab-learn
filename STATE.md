# Stand

**11.11.2026, Fassung 2: Python im Browser, live auf Vercel (Import durch den Autor).**
Repository: github.com/Lightrunnerwastaken/spotlab-learn (öffentlich).

Fertig:
- Kapitel 1–7 geschrieben (Einführung, Hallo Spot, Bewegen, Zustand, Umgebung,
  Hindernissen ausweichen, Objekte finden). Kapitel 8–14 als Vorschau (`bald: ja`).
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
- `tests/kurs_pruefen.py` nimmt denselben Motor: 53 von 53 in Ordnung (20 s).
- Im Browser geprüft: Beispiel aus Kapitel 3, Türaufgabe aus Kapitel 6 (vier Starts,
  alle Ziele erfüllt). Erster Start lädt Python etwa 20 s, danach Sekunden.

Offen:
- Kapitel 8 (Projekt: unbekannten Raum erkunden).
- Kapitel 9–11 brauchen Kamera/Tiefe: im Browser nur mit dem 2D-Sim, MuJoCo läuft dort nicht.
- Der Autor hat den Kurs noch nicht selbst durchgespielt.
