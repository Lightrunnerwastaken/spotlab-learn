---
nummer: 14
titel: Am echten Spot
---

# Vom Übungsraum zum Roboter

Alles, was du in diesem Kurs geschrieben hast, ist echter spotlab-Code. Derselbe Code läuft am echten Spot. Mit dem Knopf **⬇** neben «Ausführen» lädst du jedes Programm als `.py`-Datei herunter.

Am Schul-Laptop arbeitest du in der **spotlab-App** (Desktop-Verknüpfung «Spotlab»). Im Reiter «Code» wählst du über dem Editor, wo dein Programm läuft:

- **Übungsraum 3D (Wiedergabe):** ein Simulator mit gerendertem Spot und Kamerabildern. Daraus stammen die Bilder in Kapitel 10. Das ist die Vorgabe, wenn der 3D-Übungsraum auf dem Laptop installiert ist; sonst fehlen die beiden 3D-Einträge, und der 2D-Übungsraum ist die Vorgabe.
- **Übungsraum (virtuell):** der 2D-Simulator, den du aus diesem Kurs kennst.
- **Trockenlauf (nur Text):** nichts bewegt sich, spotlab prüft nur die Befehle (mehr dazu gleich).
- **Physik 3D:** ein Versuch mit echter Physik, nur für ebene Räume.
- **Echter Spot:** der Roboter.

Wer nichts einstellt, landet nie am echten Spot: Er steht in der Auswahl absichtlich ganz unten, und die Vorgabe ist ein Übungsraum. Den Roboter musst du **ausdrücklich** wählen.

Ein guter Ablauf für jedes neue Programm:

1. Im Übungsraum testen, bis es tut, was es soll.
2. Im **Trockenlauf** (in der Auswahl, oder `spotlab run programm.py --dryrun`): spotlab baut jeden Befehl genau so, wie er an den Roboter ginge, und prüft ihn, schickt aber nichts. Fehler wie ein Tippfehler im Befehl fallen hier auf, ohne dass sich etwas bewegt.
3. Erst dann am echten Spot, mit Aufsicht.

Nicht alles, was der Roboter kann, kann der Übungsraum, und umgekehrt kann nicht jeder Spot alles (es hängt davon ab, welche Teile eingebaut sind). Darum gibt es `supports()`: Am echten Spot fragt es den Roboter selbst, hier fragt es den Simulator.

```spot raum=leer
from spotlab import connect

with connect() as spot:
    for faehigkeit in ["look", "tags", "stairs", "camera", "navigate_to", "pose", "lights", "beep"]:
        print(f"{faehigkeit:12} {spot.supports(faehigkeit)}")
    print(f"Akku: {spot.battery:.0f} %")
```

Ein Programm, das am echten Spot und im Übungsraum funktionieren soll, fragt vorher mit `supports()` nach, wie in Kapitel 9.

```quiz punkte=2
? Dein Programm läuft im Übungsraum fehlerfrei. Du stellst in der App auf «Echter Spot» und startest es. Spot steht auf, und dann passiert etwas, das du nicht erwartet hast. Was hättest du vorher tun sollen?
A) Nichts, im Übungsraum hat es ja funktioniert.
B)* Es zuerst im Trockenlauf prüfen und beim ersten echten Start die Hand am Not-Aus haben. Der Übungsraum ist eine Vereinfachung, der echte Spot rutscht, sieht anders und reagiert anders.
C) Das Programm im 3D-Übungsraum testen, dann ist es sicher.
D) Das Tempo im Programm verdoppeln, damit es schneller vorbei ist.
! Der Simulator ist aus Messungen am echten Spot gebaut, aber er ist nicht der Roboter: Der 2D-Übungsraum kennt keine Physik, nichts kann umfallen oder rutschen, und die Kameras sind gerendert. Deshalb der Ablauf Übungsraum, Trockenlauf, Roboter, und am Roboter immer mit jemandem, der den Not-Aus drücken kann.
```

# Lease und Not-Aus

Am echten Spot passiert beim `connect()` mehr als im Übungsraum. spotlab macht vier Dinge, bevor dein Programm die erste Zeile ausführt:

1. **Anmelden** mit Benutzername und Passwort. Die Zugangsdaten hinterlegt die Lehrperson einmal im Reiter «Spot» der App.
2. **Die Uhr abgleichen.** Jeder Befehl trägt eine Ablaufzeit («gilt bis 14:03:12.5»). Gehen Laptop und Roboter verschieden, liefe jeder Befehl schon abgelaufen ein.
3. **Einen Not-Aus anmelden.** spotlab meldet sich beim Roboter als zusätzlicher Not-Aus an. Der Not-Aus am **Tablet bleibt** dabei wirksam. Hört der Roboter von spotlab nichts mehr, zum Beispiel weil der Laptop abstürzt, schaltet er von selbst in den sicheren Zustand.
4. **Das Lease holen.** Das Lease ist die **Steuererlaubnis**: Nur wer es hat, darf Spot bewegen, und es gibt genau eines. Fährt jemand mit dem Tablet, hat das Tablet das Lease, und dein Programm bekommt es nicht.

Die Motoren schaltet `connect()` **nicht** ein. Dafür steht in jedem Programm `spot.power_on()` als eigene Zeile: Ein 30-kg-Roboter soll nicht aufstehen, nur weil jemand ein Programm geöffnet hat.

Am Ende des `with`-Blocks räumt spotlab auf, auch wenn dein Programm mit einem Fehler abbricht: anhalten, hinsetzen, Motoren aus, Lease zurückgeben, Not-Aus abmelden. Wird das Programm hart beendet (zum Beispiel mit dem roten **NOT-AUS**-Knopf oben in der App), kommt es nicht mehr zum Aufräumen. Dann bleibt der Roboter trotzdem sicher, weil die Lebenszeichen ausbleiben und er von selbst in den sicheren Zustand geht.

Danach steht allerdings ein «toter» Halter im Lease, und der nächste Start meldet, dass jemand anderes Spot steuert. spotlab erkennt diesen Fall und sagt dann «es steuert niemand». Übernehmen kannst du das Lease im Reiter «Fahren» mit dem Häkchen **«Kontrolle übernehmen»**. Das ist absichtlich ein Häkchen und geschieht nie von selbst: Wer übernimmt, nimmt jemand anderem die Steuerung weg, und das soll eine bewusste Entscheidung sein.

> **Für die Lehrperson:** Vor dem ersten Einsatz mit Schülerinnen und Schülern die Abnahmeliste in spotlab abarbeiten (`docs/ABNAHME.md`), vor allem Punkt **A1**: Wirkt der Not-Aus am Tablet, während ein spotlab-Programm läuft? Und für Anfängerstunden im Reiter «Spot» das Höchsttempo von 0.6 auf 0.2 m/s stellen. Der Deckel gilt für jedes Programm, und kein Programm kann ihn überschreiben.

```quiz punkte=2
? Du startest dein Programm, und es bricht sofort ab. In der Meldung steht, dass jemand anderes Spot gerade steuert und du dich erst absprechen sollst. Am Tablet sitzt deine Lehrperson und hat gerade Spot zur Tür gefahren. Was tust du?
A) Im Reiter «Fahren» «Kontrolle übernehmen» anklicken und nochmals starten.
B)* Mit der Lehrperson absprechen. Wenn sie mit dem Tablet fertig ist und die Steuerung abgibt, startest du nochmals.
C) Den Laptop neu starten.
D) Das Programm mit `--dryrun` starten.
! Die Meldung sagt die Wahrheit: Das Tablet hat das Lease. Übernehmen würde der Lehrperson die Steuerung mitten in der Fahrt wegnehmen. «Kontrolle übernehmen» ist für den Fall gedacht, in dem **niemand** mehr steuert, zum Beispiel nach einem Not-Aus, wenn ein abgestürztes Programm das Lease noch hält. spotlab unterscheidet die beiden Fälle in der Meldung.
```

```quiz punkte=2
? Mitten in deinem Programm, während Spot geht, tritt ein Fehler auf: `ZeroDivisionError`. Was macht Spot?
A) Er geht mit dem letzten Befehl weiter, bis der Akku leer ist.
B) Er bleibt stehend, wo er ist, mit eingeschalteten Motoren.
C)* Er hält an, setzt sich hin und schaltet die Motoren aus, weil spotlab beim Verlassen des `with`-Blocks immer aufräumt.
D) Er fällt um.
! Der `with`-Block ist genau dafür da: Egal wie er verlassen wird, ob am Ende, durch einen Fehler oder durch Strg+C, spotlab räumt auf. Und selbst wenn das nicht mehr geht, laufen Fahrbefehle nach etwa einer Sekunde ab (Kapitel 12), und ohne Lebenszeichen geht der Roboter in den sicheren Zustand.
```

# Akku wechseln und aufrichten

Zwei Dinge macht man am echten Spot öfter: den Akku wechseln und Spot wieder aufrichten, wenn er umgefallen ist. Für beides hat der Reiter «Fahren» einen eigenen Knopf. Sie starten fertige Programme aus spotlab, die nicht im Arbeitsordner liegen und die deshalb niemand aus Versehen verändern kann.

- **🔋 Akku wechseln:** Spot legt sich auf die Seite, links oder rechts, sodass das Akkufach unten erreichbar ist. Danach schaltet er die Motoren **selbst** aus. Ob es geklappt hat, misst spotlab am Rollwinkel des Körpers, also daran, wie weit er auf der Seite liegt.
- **⬆ Aufrichten:** Liegt Spot auf der Seite oder auf dem Rücken, dreht er sich zurück auf die Füsse und setzt sich hin.

Beide Knöpfe gehen nur, wenn **kein anderes Programm läuft**: Ein fahrender Roboter soll sich nicht auf Knopfdruck hinlegen. Und die Motoren müssen vorher aus sein.

Den Akkustand liest dein Programm mit `spot.battery`, in Prozent. Ein Programm, das lange läuft, prüft ihn am Anfang:

```spot raum=leer
from spotlab import connect

MINDESTENS = 30           # Prozent

with connect() as spot:
    if spot.battery < MINDESTENS:
        print(f"Akku nur {spot.battery:.0f} %, bitte zuerst laden.")
    else:
        print(f"Akku {spot.battery:.0f} %, los geht's.")
        spot.power_on()
        spot.stand()
```

```quiz punkte=2
? Nach «Akku wechseln» meldet spotlab: «Motoren unerwartet aus — liegt NICHT auf der Seite». Was ist wahrscheinlich passiert?
A) Der Akkuwechsel hat ganz normal geklappt.
B)* Spot hat sich nicht auf die Seite gelegt, die Motoren sind aus einem anderen Grund aus, zum Beispiel weil jemand den Not-Aus am Tablet gedrückt hat. Zuerst nachsehen, bevor man den Akku herausnimmt.
C) Der Akku ist schon herausgenommen.
D) spotlab hat sich verrechnet, man kann die Meldung übergehen.
! Spot schaltet beim Akkuwechsel die Motoren selbst aus. «Motoren aus» allein sagt also noch nicht, dass er auf der Seite liegt. spotlab prüft darum den Rollwinkel: Liegt Spot nicht weit genug auf der Seite, ist etwas anderes passiert, und die Meldung sagt das, statt einen Erfolg zu behaupten.
```

# Läufe auswerten

spotlab schreibt bei **jedem** Lauf alles mit, im Übungsraum wie am echten Spot: jeden Befehl, jede Rückmeldung und laufend den Zustand des Roboters. Jeder Lauf bekommt einen eigenen Ordner unter `runs/` neben deinem Programm:

- `lauf.json`: wann, welches Programm, wo (Übungsraum oder Roboter), wie es ausging
- `ereignisse.jsonl`: jeder Befehl und jede Rückmeldung, mit Zeit
- `zustand.jsonl`: der Zustand des Roboters, zehnmal pro Sekunde: Lage, Tempo, alle 12 Gelenke, Akku
- `bilder/`: die Bilder, die dein Programm mit `spot.camera(...)` geholt hat

Jede Zeile in den `.jsonl`-Dateien ist ein Dictionary im JSON-Format. Dein Programm kann seine eigene Aufzeichnung sogar lesen, während es läuft: `spot.recorder.dir` ist der Ordner des Laufs. Hier geht Spot 2 Sekunden mit 0.5 m/s und schaut danach nach, was wirklich passiert ist:

```spot raum=leer
import json, time
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    spot.walk(vx=0.5, duration=2)
    time.sleep(1)                              # warten, bis Spot ausgelaufen ist
    datei = spot.recorder.dir / "zustand.jsonl"
    for zeile in datei.read_text().splitlines():
        z = json.loads(zeile)
        x = z["daten"]["pose"][0]
        tempo = z["daten"]["velocity"][0]
        print(f"t = {z['t']:4.1f} s   x = {x:4.2f} m   Tempo {tempo:4.2f} m/s")
```

Befohlen waren 0.5 m/s für 2 Sekunden, also 1 m. Gemessen kommt Spot von x = 1.00 bis x = 1.87, nur 0.87 m weit. Am Anfang braucht er fast eine Sekunde, bis er das volle Tempo erreicht, das siehst du in den ersten Zeilen. Am Ende läuft er nach dem Stopp noch kurz aus. Genau solche Unterschiede zwischen **befohlen** und **gemessen** zeigt der Reiter «Läufe» der App als Kurve, für jeden vergangenen Lauf.

> Im Kurs wird der Zustand fünfmal pro Sekunde aufgeschrieben statt zehnmal, damit es im Browser schneller geht. In der spotlab-App sind es zehn.

```quiz punkte=2
? Ein Programm hat Spot am echten Roboter in eine Wand gefahren. Du willst herausfinden, welcher Befehl zuletzt geschickt wurde und wie schnell Spot da war. Wo schaust du nach?
A) Nur in `lauf.json`.
B)* In `ereignisse.jsonl` den letzten Befehl, und in `zustand.jsonl` zur selben Zeit das Tempo. Beide haben dieselbe Zeitangabe `t`.
C) In `bilder/`.
D) Gar nicht, am echten Spot wird nichts aufgezeichnet.
! Befehle stehen in `ereignisse.jsonl`, der gemessene Zustand in `zustand.jsonl`. Beide zählen die Zeit `t` ab dem Start desselben Laufs, darum kann man sie nebeneinanderlegen: «um 12.4 s kam `walk(vx=0.5)`, um 12.6 s war das gemessene Tempo 0.48 m/s». So findet man heraus, ob der Fehler im Programm lag oder am Roboter.
```

# Ein Experiment: die Gehzeit

Spot ist nicht nur ein Roboter, den man programmiert. Er ist auch ein **Messgerät**. spotlab hat dafür ein fertiges Experiment, im Reiter «Experimente» der App: die **Gehzeit**.

Die Frage stammt aus der Verhaltensbiologie: Wie schnell gehen Menschen, und hängt das davon ab, ob sie allein oder in einer Gruppe gehen? Mit einer Stoppuhr misst man immer nur eine Person auf einmal. Spot misst alle gleichzeitig.

So läuft es:

- An die beiden Enden einer Strecke im Gang kommt je ein AprilTag. Spot steht seitlich so, dass er beide sieht.
- **Spot misst die Strecke selbst**, aus den zwei Tags, mehrmals, und nimmt den mittleren Wert. Niemand tippt eine Länge ein.
- Jede Person trägt einen Tag am Rucksack. Spot stoppt für jede die Zeit von der einen Linie bis zur anderen und rechnet das Tempo aus.
- Wer stehen bleibt, umkehrt oder verschwindet, wird **verworfen**, mit Grund in der Tabelle.
- Ob drei Personen eine Gruppe waren, kann Spot nicht wissen. Er schlägt vor, wer gleichzeitig unterwegs war, und zeigt Bilder dazu. Die Gruppengrösse trägt **ein Mensch** nach.
- Am Schluss fragt das Programm, ob die Bilder gelöscht werden sollen. Es sind Aufnahmen von Mitschülerinnen und Mitschülern, gemacht für genau eine Frage.

Spot bewegt sich bei diesem Experiment nicht, und er nimmt sich auch kein Lease. Er verbindet sich nur zum Lesen (`connect(nur_lesen=True)`), und die Aufsicht behält das Tablet.

```quiz punkte=2
? Warum misst Spot die Strecke zwischen den Tags jedes Mal selbst, statt dass man sie einmal mit dem Massband misst und eintippt?
A) Weil Spot genauer misst als ein Massband.
B)* Weil am nächsten Tag jemand die Tags woanders hingehängt haben könnte. Dann stimmte der eingetippte Wert nicht mehr, und jedes Tempo wäre falsch, ohne dass es jemand merkt.
C) Weil Tippen zu lange dauert.
D) Weil Spot keine Zahlen von Hand annimmt.
! Ein eingetippter Wert sieht immer richtig aus, auch wenn er nicht mehr stimmt: Die Zeiten wären echt, die Strecke falsch, und alle Tempos wären um denselben Faktor daneben. Gemessen wird deshalb bei jedem Versuch neu, und die Streuung der Messungen steht daneben. Wird sie zu gross, lehnt das Programm ab, statt mit einer wackligen Länge zu rechnen.
```

```quiz punkte=2
? Spot könnte aus den Bildern auch das Alter der Personen schätzen, damit man «Jugendliche gegen Erwachsene» vergleichen kann. spotlab macht das absichtlich nicht. Welcher Grund passt am besten?
A) Weil es verboten ist, Bilder zu machen.
B) Weil Spot keine Gesichter sehen kann.
C)* Weil eine unsichere Schätzung in derselben Tabelle wie die gemessenen Zeiten stünde und genauso zuverlässig aussähe. Beim Testen hat der Gesichtserkenner sogar eine Stuhllehne und ein Schienbein für Gesichter gehalten.
D) Weil das Alter nichts mit dem Tempo zu tun hat.
! Ein Experiment ist nur so gut wie seine schwächste Zahl. Zeiten und Strecke sind gemessen und haben eine bekannte Ungenauigkeit. Eine Altersschätzung aus einem Kamerabild wäre eine Vermutung, die in der Tabelle aussieht wie eine Messung. spotlab liefert darum Messwerte und überlässt Urteile, wie die Gruppengrösse, einem Menschen.
```

# Wie es weitergeht

Du kennst jetzt alles, was du für eigene Spot-Projekte brauchst: Bewegen, Wahrnehmen, Ausweichen, Objekte finden, Erkunden, Licht und Ton, Kameras, Karten, Folgen und Treppen. Ein paar Ideen für ein eigenes Projekt:

- **Hausmeister:** Spot geht jeden Abend eine Runde durch den Gang und meldet, welche Tags fehlen oder an einem anderen Ort hängen.
- **Wegweiser:** Spot führt Besucher vom Eingang zur Bibliothek: er geht voraus, wartet, wenn der Mensch zurückbleibt (Kapitel 12 andersherum), und zeigt mit Licht, ob es weitergeht.
- **Vermesser:** Spot erkundet ein leeres Zimmer (Kapitel 8 und 11) und gibt am Ende Länge und Breite aus.
- **Messgerät:** Ein eigenes Experiment wie die Gehzeit, zum Beispiel wie oft eine Tür in einer Pause aufgeht.

Bau jedes Projekt zuerst im Übungsraum. Der Raumeditor der spotlab-App baut dir dafür jeden Raum, den du brauchst.
