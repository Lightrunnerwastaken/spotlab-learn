# Spot programmieren — der Kurs zu spotlab

Eine Lernplattform für Schülerinnen und Schüler, die den Roboterhund Spot mit
[spotlab](https://github.com/Lightrunnerwastaken/spotlab) programmieren lernen.
Aufbau wie ki-kurs.org: Kapitelkarten, Lektionen mit «Zurück»/«Weiter», Code
zum Ausführen, Quizfragen mit drei Versuchen.

- **Der Code läuft mit dem echten spotlab-Simulator — im Browser.** Python
  (Pyodide) rechnet auf dem Gerät der Schüler; es gibt keinen Server, der
  fremden Code ausführt. Eine Karte zeigt den Übungsraum von oben, Spots Weg
  wird abgespielt.
- **Aufgaben werden automatisch geprüft:** Wo steht Spot am Ende, schaut er in
  die richtige Richtung, ist er angestossen, steht der richtige Text in der
  Ausgabe? Navigationsaufgaben laufen von **mehreren Startplätzen** gleichzeitig:
  ein auswendig gelernter Weg besteht dort nicht, nur ein Programm, das hinschaut.
- **Quizfragen fragen nach Anwendung**, nicht nach Auswendiggelerntem. Volle
  Punkte gibt es nur beim ersten Versuch.

## Wie es läuft

```
web/                    die Webseite (statisch, so liefert Vercel sie aus)
  index.html, app.js    Übersicht, Lektionen, Codefelder, Quiz, Aufgaben, Karte
  motor.js              Web Worker: lädt Pyodide, numpy, protobuf, bosdyn (von PyPI)
                        und py/kurs-python.zip, führt den Code aus
  kurs.json             erzeugt aus kurs/*.md
  raeume/*.json         Grundrisse der Übungsräume, erzeugt aus spotlab
  py/kurs-python.zip    spotlab (ohne GUI) und motor/kursmotor.py, erzeugt
motor/kursmotor.py      führt Schülercode mit spotlab aus: virtuelle Uhr, Abtaster
                        ohne Thread, Attrappen für die Netzpakete des echten Roboters
kurs/*.md               die Kapitel
tests/kurs_pruefen.py   prüft jedes Beispiel und jede Aufgabe mit demselben Motor
tests/loesungen/        Musterlösungen der Aufgaben (für Lehrpersonen)
baue.py                 erzeugt kurs.json, raeume/ und py/kurs-python.zip
server.py               lokaler Server zum Schreiben am Kurs
```

Der Kursmotor stellt eine **virtuelle Uhr**: `time.sleep(2)` stellt sie um 2 s
vor, statt zu warten. Der Simulator rechnet in kleinen Schritten bis zur
aktuellen Zeit und merkt davon nichts. Ein Lauf von einer Minute Spot-Zeit ist
so in ein bis drei Sekunden gerechnet; die Seite spielt ihn danach schneller
als echt ab.

Sicherheit: Der Motor setzt `SPOTLAB_NUR_TROCKEN=1` vor dem ersten Import von
spotlab. Dann weist spotlab jedes Backend ab, das einen Roboter erreichen kann.

bosdyn (das Spot-SDK von Boston Dynamics) ist nicht frei lizenziert und liegt
deshalb nicht in diesem Repository. Der Browser lädt es beim ersten Start
selbst von PyPI.

## Auf Vercel

Das Repository enthält alle erzeugten Dateien; Vercel baut nichts, es liefert
nur `web/` aus (`vercel.json`). Neues Projekt in Vercel → dieses Repository
importieren → Deploy. Jeder Push auf `main` veröffentlicht neu.

## Am Kurs schreiben

Mit dem Python, in dem spotlab installiert ist:

```powershell
python server.py        # baut einmal alles, dann http://127.0.0.1:5200
```

Kapitel sind Textdateien in `kurs/`; die Seite liest sie bei jedem Laden neu.
Die Schreibweise steht oben in [kursparser.py](kursparser.py). Kurz:

- `# Titel` beginnt einen Abschnitt (eine Seite).
- ```` ```spot raum=moebliert ```` … ```` ``` ```` ist ein Codefeld mit Karte.
- ```` ```quiz ```` mit `?` Frage, `A)` … `D)` Antworten, `*` an der richtigen, `!` Erklärung.
  Zeilen mit `|` am Anfang sind Code im Fragetext.
- ```` ```aufgabe ```` mit `ziel:`-Zeilen, `tipp:`-Zeilen, `---`, Startcode.
  Mit `starts=1,3.2,0;1,0.8,0` im Kopf läuft das Programm von jedem Startplatz aus und
  muss überall bestehen.

Vor dem Hochladen:

```powershell
python tests\kurs_pruefen.py     # jedes Beispiel, jede Aufgabe, jede Quiz-Aussage
python baue.py                   # web/ neu erzeugen, dann committen
```

Die Musterlösungen heissen `<kapitel>-<abschnitt>-<block>.py`, gezählt ab 0.

Was beim Bau des Kurses an spotlab auffiel: [BEFUNDE_SPOTLAB.md](BEFUNDE_SPOTLAB.md).
