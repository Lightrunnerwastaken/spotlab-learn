# Stand

**11.11.2026, Fassung 2: Python im Browser, bereit für Vercel.**
Repository: github.com/Lightrunnerwastaken/spotlab-learn (öffentlich).

Fertig:
- Kapitel 1–6 geschrieben (Einführung, Hallo Spot, Bewegen, Zustand, Umgebung,
  Hindernissen ausweichen). Kapitel 7–14 als Vorschau (`bald: ja`).
- Der Schülercode läuft im Browser: Pyodide 0.27.7 im Web Worker (`web/motor.js`),
  numpy/protobuf/wrapt aus Pyodide, bosdyn 5.0.1.2 von PyPI (nicht frei lizenziert,
  darum nicht im Repo), spotlab + `motor/kursmotor.py` aus `web/py/kurs-python.zip`.
- Kursmotor: virtuelle Uhr (Lauf von 70 s Spot-Zeit in ~3 s gerechnet), Abtaster ohne
  Thread, Attrappen für grpc/jwt/cryptography/urllib3/requests/keyring/pynmea2.
  Gegen den alten Echtzeit-Server verglichen: gleiche Wege, gleiche Zeiten.
- Aufgaben mit mehreren Startplätzen (`starts=`), Ziel `ende_in`, Hinweis beim Anstossen.
- `tests/kurs_pruefen.py` nimmt denselben Motor: 38 von 38 in Ordnung (19 s).
- Im Browser geprüft: Beispiel aus Kapitel 3, Türaufgabe aus Kapitel 6 (vier Starts,
  alle Ziele erfüllt). Erster Start lädt Python etwa 20 s, danach Sekunden.

Offen:
- Kapitel 7 (Objekte finden): braucht einen Tag näher als 3 m (Befund 3), dann 8 (Projekt).
- Kapitel 9–11 brauchen Kamera/Tiefe: im Browser nur mit dem 2D-Sim, MuJoCo läuft dort nicht.
- Der Autor hat den Kurs noch nicht selbst durchgespielt.
