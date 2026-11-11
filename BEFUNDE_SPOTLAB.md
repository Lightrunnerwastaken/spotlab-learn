# Was beim Bau des Kurses an spotlab auffiel

Gesammelt beim Schreiben der Lektionen, jeweils im Simulator (Backend `sim`)
nachgeprüft. Für eine gute Lernerfahrung sollte spotlab hier nachziehen.
Nichts davon ist in spotlab geändert, nur festgehalten.

## 1. `spot.look()` sagt ohne Angabe überall «unknown»

Mit der Vorgabe `start=0.0` ist im Sim in **allen vier Richtungen** der Status
`unknown` (`tests/kurs_pruefen.py` prüft das nach). Grund ist der Körperschatten
von 0.5 m. Das ist ehrlich, aber der allererste Aufruf eines Anfängers liefert
damit nur «weiss nicht». Im Kurs muss deshalb jedes Beispiel `start=0.6`
schreiben, und Kapitel 5 braucht einen ganzen Abschnitt, um das zu erklären.

Vorschlag: Die Vorgabe auf den Körperrand setzen (`start=0.6`) **oder** bei
`unknown` im Nahbereich einen eigenen Status wie `shadow` melden, damit man es
von «da ist nichts bekannt» unterscheiden kann.

## 2. Anstossen mit `move()` gibt eine irreführende Meldung

Läuft Spot mit `move(forward=6)` in eine Wand, endet das Programm mit

    CommandRejected: Der Roboter hat das Kommando 'ankommen' abgelehnt: abgelaufen (Sim)

Das Ereignis `angestossen` steht zwar in der Aufzeichnung, sogar mit Ort und
Name des Hindernisses (`{"x": 1.79, "y": 2.6, "hindernis": "Kiste"}`), aber die
Meldung sagt nichts davon. Ein Schüler sucht den Fehler dann in seinem Code.
Vorschlag: im Sim die Meldung «Spot ist bei x=…, y=… an «Kiste» gestossen»
ausgeben. **Der Kurs macht das seit Kapitel 6 selbst** (`motor/kursmotor.py`, Feld
`hinweis`), spotlab sollte es aber direkt tun — im GUI fehlt es weiter.

## 3. In den Übungsräumen sieht Spot vom Start aus keinen Tag

Im Raum «Möbliert» liefert `spot.tags()` vom Startplatz aus in **keiner** von
acht Blickrichtungen (alle 45°) einen Tag. Geklärt beim Bau von Kapitel 6: Im
Raum «Durchgang» sieht Spot Tag 3 erst ab rund 2.9 m Abstand. Die Tags in
«Möbliert» hängen vom Start aus 3.6 m und weiter weg — zu weit. Die Reichweite ist
`TAG_REICHWEITE_M = 3.0` in `welt/wahrnehmung.py`, laut Kommentar dort **geschätzt,
nicht gemessen** (Abnahmepunkt A22). Kapitel 7 löst es mit eigenen Startplätzen
(Raummitte 3.5, 2.7: beide Tags in Sicht) und macht die Grenze zum Lernstoff
(«aus der Ecke sieht Spot keinen Tag, Drehen hilft nicht»). Vorschlag: der
Vorgabestart von «Möbliert» näher an einen Tag, damit `tags()` beim ersten Versuch
etwas liefert; und A22 messen, damit der Kurs eine echte Zahl nennen kann.

Dazu, nicht falsch, aber nirgends gesagt: Der Sim sieht Tags **rundum** (kein
Blickkegel, fünf Kameras). Wer vom Handy her denkt, sucht durch Drehen — im Sim
ändert Drehen nichts. Ob der echte Spot nach hinten genauso weit sieht wie nach
vorne, ist nicht geprüft.

## 3b. Das Hindernisgitter reicht nur 1.9 m weit

128 × 128 Zellen à 3 cm, also ein Quadrat von 3.84 m um Spot (wie am echten
Spot). `look(max_distance=…)` nimmt aber Werte bis 10 m an und meldet dann ab
1.9 m `unknown`, ohne Hinweis. Vorschlag: in der Doku von `look` die Reichweite
nennen oder bei `max_distance` über dem Gitterrand einmal warnen.

## 3c. `look` prüft ab `start`, Spot ist breiter als der Strahl

Mit `margin=0.3` (Vorgabe) meldet `look` vorne `clear`, obwohl eine Kistenecke
schräg vor Spot im ungeprüften Nahbereich liegt; ein Schritt von 0.3 m stösst an
(Kapitel 6, im Kurs nachgeprüft). `margin=0.35` reicht dort. Mit 0.4 kommt Spot
durch die 90-cm-Tür im Raum «Durchgang» nur noch nach langem Suchen. Die
Vorgabe 0.3 liegt sehr nahe an Spots halber Breite (0.27 m im Sim).

## 4. Kamera, Licht, Ton, Haltung und Navigation fehlen im 2D-Sim

`supports()` im Sim mit Raum: `look`, `tags`, `stairs` ja; `camera`,
`navigate_to`, `pose`, `lights`, `beep` nein. Für die Kapitel 9–11 braucht der
Kurs deshalb `mujoco`/`physics` (Kamera, Tiefe) oder `dryrun` (Licht, Ton,
Haltung prüfen nur die Befehle). Karten aufnehmen und navigieren geht nur am
echten Spot. Offen: ob der Kurs MuJoCo-Läufe im Browser zeigen soll (langsamer
Start, Kamerabilder statt Draufsicht).

## 4b. `look()` kostet im 2D-Sim 0.2 s Rechenzeit

Gemessen beim Bau von Kapitel 8 (11.11.2026, CPython, Raum «Wohnung» mit 8 Wänden
und 3 Hindernissen): ein `look()` braucht rund 0.2 s, fast alles in
`welt/wahrnehmung.py::abstandsgitter` → `kollision.sicht_frei` (1024 Sichtlinien je
Aufruf, 125 000 Schnitttests in reinem Python). Ein Erkundungsprogramm ruft `look`
bei jedem Schritt; 80 Schritte sind 16 s nur für die Sicht, im Browser (Pyodide)
mehr. Der Kurs lebt damit (Schritte von 0.5 m, Notbremse 80), ändert aber nichts an
spotlab. Vorschlag: die Sichtprüfung mit numpy vektorisieren (die Abstände tun es
schon) oder je Pose zwischenspeichern, solange der Raum gleich bleibt.

Der Kursmotor spart dafür an der Aufzeichnung: `fsync` nach jeder Zeile
(`record/run.py::_zeile`) ist im Kurs aus, und der Zustand wird mit 5 statt 10 Hz
mitgeschrieben. Zusammen halbierte das die Rechenzeit, ohne dass sich ein Weg
änderte (alle 53 Prüfungen der Kapitel 1–7 blieben gleich).

## 4c. Im Trockenlauf kehren `lights()` und `beep()` sofort zurück

Am echten Spot wartet `api/signals.py::_run` die Dauer ab (`time.sleep(duration)`),
im Trockenlauf (`spot.robot is None`) kehrt es nach dem Protobuf-Check sofort zurück.
Ein Programm, das am Gerät 5 s lang blinkt, ist im Trockenlauf in null Sekunden
vorbei, und alle Signale tragen denselben Zeitstempel. Wer den Trockenlauf nutzt,
um ein Programm zu Hause zu prüfen («spotlab run --dryrun»), sieht damit ein
anderes Zeitverhalten als am Gerät. Der Kurs gleicht es aus
(`kursmotor.trockenlauf_wie_am_geraet`: schläft die Dauer auf der virtuellen Uhr,
nach `pose()` 1 s als Annahme). Vorschlag: im Trockenlauf ebenfalls schlafen.

Dazu, für Kapitel 9 festgehalten: Notennamen sind englisch (`"B"` ist das deutsche
H, `beep("H")` gibt einen ValueError), und `pose()` beschreibt die ganze Haltung,
nicht eine Änderung — beides ist richtig, aber eine Falle für deutschsprachige
Anfänger, die der Kurs ausdrücklich erklärt.

## 5. Kleinigkeiten

- `walk(vx=0.5, duration=2)` bringt Spot im Sim 0.77 m weit (Anlaufen und
  Bremsen). Richtig und lehrreich, steht aber nirgends in der API-Beschreibung.
- `spot.state.heading` nach `move(turn=90)` ist 89.9. Gut zum Lernen («befohlen
  ist nicht gemessen»), Kapitel 4 baut darauf auf.
- `move()` geht im Sim auch, während Spot sitzt. Ob der echte Spot dabei
  aufsteht oder ablehnt, ist hier nicht geprüft; der Sim sollte dasselbe tun wie
  das Gerät.
- spotlab hat keinen eigenen Befehl, um den Kurs zu starten. Später passt
  `spotlab kurs` gut neben `spotlab gui`, dann braucht es `starten.ps1` nicht.
