---
nummer: 9
titel: Licht, Ton und Haltung
---

# Die LEDs

Spot kann zeigen, was er gerade tut: mit farbigen **LEDs** vorne und hinten am Körper. Das ist wichtig für die Menschen um ihn herum. Wer vor Spot steht, sieht nicht auf den Laptop, aber er sieht, ob Spot grün oder rot leuchtet.

Die Übungsräume aus den Kapiteln 1 bis 8 haben keine Lichter. In diesem Kapitel läuft dein Programm deshalb im **Trockenlauf**: spotlab baut alle Befehle genau so, wie sie an den echten Spot gingen, prüft sie, und rechts zeigt eine Zeichnung, was Spot damit täte. Mit dem Lautsprecher-Knopf unter der Zeichnung schaltest du den Ton ein oder aus.

Eine Ampel:

```spot raum=trocken
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    spot.lights("red", duration=2)
    spot.lights("yellow", duration=1)
    spot.lights("green", duration=2)
    print("Ampel fertig")
```

`spot.lights(farbe, duration=..., brightness=...)` hat drei Teile:

- **Farbe:** `"blue"`, `"green"`, `"red"`, `"white"`, `"yellow"` oder `"purple"`, oder eine eigene Farbe als **RGB-Tupel** `(rot, grün, blau)` mit Werten von 0 bis 255. `(255, 128, 0)` ist Orange.
- **duration:** wie lange, in Sekunden (0.05 bis 10). Danach gehen die LEDs wieder aus.
- **brightness:** wie hell, von 0 bis 1. Ohne Angabe 0.25, damit niemand geblendet wird.

Wichtig: `lights` **wartet**, bis die Zeit um ist. Erst dann geht dein Programm zur nächsten Zeile. So entsteht die Ampel: rot 2 s, dann gelb 1 s, dann grün 2 s.

Blinken heisst also: kurz leuchten, kurz warten, und das wiederholt:

```spot raum=trocken
import time
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    for i in range(5):
        spot.lights((255, 128, 0), duration=0.3, brightness=1.0)
        time.sleep(0.3)
```

```quiz punkte=2
? Was macht Spot bei diesem Programm (am echten Gerät)?
| spot.lights("red", duration=3)
| spot.move(forward=1)
A) Er leuchtet rot und geht dabei gleichzeitig 1 m vorwärts.
B)* Er leuchtet 3 Sekunden rot und steht still. Erst danach geht er 1 m.
C) Er geht 1 m und leuchtet danach 3 Sekunden rot.
D) Er leuchtet rot, solange das Programm läuft, also auch während er geht.
! `lights` wartet die ganze Dauer ab, und erst dann kommt `move` dran. Für eine Warnung vor dem Losgehen ist das genau richtig. Wer **während** einer Fahrt leuchten will, braucht etwas anderes: spotlab hat dafür ein Statuslicht, das nicht wartet (`spotlab.api.signals.Statuslicht`), das ist aber Stoff für später.
```

# Töne mit dem Summer

Spot hat einen **Summer**, der Töne spielen kann. `spot.beep(note, octave=..., duration=...)` spielt einen Ton:

- **note:** der Name des Tons, `"C"`, `"D"`, `"E"`, `"F"`, `"G"`, `"A"` oder `"B"`.
- **octave:** wie hoch, von 0 bis 8. Ohne Angabe 5.
- **duration:** wie lange, 0.05 bis 5 Sekunden. Wie `lights` wartet auch `beep`, bis der Ton fertig ist.

Eine Tonleiter:

```spot raum=trocken
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    for note in ["C", "D", "E", "F", "G", "A", "B"]:
        spot.beep(note, octave=5, duration=0.3)
    spot.beep("C", octave=6, duration=0.6)
```

Die letzte Zeile spielt wieder ein C, aber eine **Oktave höher**. Eine Oktave höher heisst doppelt so schnelle Schwingung, und es klingt wie «derselbe Ton, nur höher».

Für eine Melodie legst du die Töne in eine Liste. Jeder Ton ist ein Tupel aus Note, Oktave und Dauer, und die Schleife packt es mit drei Namen aus:

```spot raum=trocken
from spotlab import connect

melodie = [("C", 5, 0.3), ("D", 5, 0.3), ("E", 5, 0.3), ("F", 5, 0.3),
           ("G", 5, 0.6), ("G", 5, 0.6)]

with connect() as spot:
    spot.power_on()
    spot.stand()
    for note, oktave, dauer in melodie:
        spot.beep(note, octave=oktave, duration=dauer)
```

Erkennst du den Anfang von «Alle meine Entchen»?

```quiz punkte=2
? In der Musikstunde heisst die Tonleiter C D E F G A **H** C. Du willst das H auf Spot spielen. Was schreibst du?
A) `spot.beep("H")`
B)* `spot.beep("B")`
C) `spot.beep("Bb")`
D) Das geht nicht, Spot kennt nur sieben Töne ohne H.
! spotlab benutzt die **englischen** Notennamen, wie fast alle Programme und das Spot-SDK von Boston Dynamics. Dort heisst das deutsche H «B». `spot.beep("H")` gibt einen `ValueError` mit der Liste der erlaubten Namen. Eine echte Falle für deutschsprachige Programmierer: «B» heisst im Deutschen nämlich ein anderer Ton, einen Halbton tiefer als H.
```

# Den Körper neigen und heben

Spot kann seinen Körper neigen, während die Füsse stehen bleiben, zum Beispiel um zu nicken, sich zu verbeugen oder um mit den Kameras nach oben zu schauen. Das macht `spot.pose(...)`, und zwar nur **im Stehen**:

- `roll`: zur Seite kippen, −20° bis 20°
- `pitch`: Nase hoch oder runter, −20° bis 20°
- `yaw`: Körper nach links oder rechts drehen, −30° bis 30° (die Füsse bleiben, wo sie sind)
- `height`: höher oder tiefer stehen, −0.15 m bis 0.15 m

Die Vorzeichen musst du dir merken, denn sie folgen den Regeln der Robotik, nicht dem Gefühl:

- **pitch positiv senkt die Nase**, negativ hebt sie.
- **roll positiv hebt die linke Seite**, Spot kippt also nach rechts.
- **yaw positiv dreht nach links**, wie bei `move(turn=...)`.

Spot nickt:

```spot raum=trocken
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    spot.pose(pitch=15)     # Nase runter
    spot.pose(pitch=-15)    # Nase hoch
    spot.pose()             # wieder gerade
    print("genickt")
```

Ganz wichtig: Jedes `pose()` gibt die **ganze Haltung** an, nicht nur eine Änderung. Was du nicht angibst, ist 0. `spot.pose()` ohne alles heisst deshalb «wieder gerade stehen».

> Wie lange Spot für einen Haltungswechsel braucht, ist am echten Gerät noch nicht gemessen. Der Kurs rechnet mit 1 Sekunde, wie spotlabs eigener Physik-Simulator.

Werte ausserhalb der Grenzen nimmt Spot gar nicht erst an:

```spot raum=trocken fehler=ja
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    spot.pose(pitch=30)
```

Ein `ValueError` statt einer stillen Abkürzung auf 20°. So merkst du sofort, dass dein Programm etwas verlangt, das Spot nicht kann.

```quiz punkte=2
? Wie steht Spot nach diesen zwei Zeilen?
| spot.pose(pitch=10)
| spot.pose(roll=10)
A) Nase 10° runter **und** 10° nach rechts gekippt.
B)* Nur 10° nach rechts gekippt, die Nase ist wieder gerade.
C) Nur die Nase 10° runter, denn das zweite `pose` gilt erst, wenn das erste fertig ist.
D) 20° geneigt, weil sich beide Werte addieren.
! Jedes `pose()` beschreibt die ganze Haltung. Das zweite sagt: roll 10, alles andere 0. Wer beides will, schreibt es in **ein** `pose`: `spot.pose(pitch=10, roll=10)`. Das ist anders als bei `move`, wo jeder Befehl **von der aktuellen Lage aus** gilt.
```

```quiz punkte=2
? Spot steht vor einem Menschen und soll mit den Frontkameras zu dessen Gesicht hinaufschauen. Was schreibst du?
A) `spot.pose(pitch=15)`
B)* `spot.pose(pitch=-15)`
C) `spot.pose(height=0.15)`
D) `spot.pose(roll=15)`
! Hinaufschauen heisst Nase **hoch**, und das ist bei Spot ein **negativer** pitch. Höher stehen (C) hilft ein wenig, hebt aber nur um 15 cm, und der Blick bleibt flach. Genau diese Vorzeichenfrage hat beim Bau von spotlabs Folgemodus eine Rolle gespielt: Dort ist «Nase hoch ist negativ» als feste Regel im Code festgehalten.
```

# Was können welche Spots?

Nicht jeder Spot kann alles, und nicht jeder Simulator auch:

- Der **2D-Übungsraum** (Kapitel 1–8) kann gehen, `look` und `tags`, aber kein Licht, keinen Ton und kein `pose`.
- Der **Trockenlauf** (dieses Kapitel) baut jeden Befehl, bewegt aber nichts und sieht nichts Echtes.
- Ein **echter Spot** hat LEDs und Summer nur, wenn bei ihm der Dienst «audio-visual» läuft. Das hängt von seiner Software ab.

Darum gibt es `spot.supports(...)`. Es fragt, ob **dieser** Spot etwas kann, bevor du es benutzt. Hier im 2D-Übungsraum:

```spot raum=leer
from spotlab import connect

with connect() as spot:
    for faehigkeit in ["lights", "beep", "pose", "look", "tags", "camera"]:
        print(faehigkeit, spot.supports(faehigkeit))
```

Wer `lights` trotzdem aufruft, bekommt einen Fehler:

```spot raum=leer fehler=ja
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    spot.lights("green")
    print("Das kommt nie.")
```

Ein Programm, das auf **jedem** Spot laufen soll, fragt vorher:

```python
if spot.supports("lights"):
    spot.lights("green", duration=1)
else:
    print("(kein Licht, weiter ohne)")
```

## Aufgabe 1: Spot begrüsst dich

Schreib eine Begrüssung, die im Trockenlauf genau so abläuft:

1. Spot steht auf und leuchtet 1 s **blau**.
2. Er spielt den Dreiklang **C5, E5, G5**, jeden Ton 0.3 s.
3. Er nickt: Nase 15° runter, dann wieder gerade.
4. Er leuchtet 1 s **grün**, setzt sich hin und gibt `Begrüssung fertig` aus.

```aufgabe raum=trocken punkte=6
ziel: licht blue green
ziel: toene C5 E5 G5
ziel: haltung pitch 15
ziel: sitzt
ziel: ausgabe Begrüssung fertig
tipp: Die Haltung nach dem Nicken ist `spot.pose()` ohne Werte. Hinsetzen geht mit `spot.sit()`.
tipp: «Nase runter» ist ein **positiver** pitch.
---
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    # 1. blau

    # 2. Dreiklang

    # 3. nicken

    # 4. grün, hinsetzen
```

## Aufgabe 2: Läuft überall

Jetzt läuft dieselbe Begrüssung im **2D-Übungsraum**, wo es kein Licht, keinen Summer und kein `pose` gibt. Der Startcode unten ist eine Lösung von Aufgabe 1. Hier stürzt er gleich bei `lights` ab.

Ändere das Programm so, dass es **überall** läuft: Was der Spot kann, macht er, und den Rest lässt er weg. Am Ende sitzt Spot und gibt `Begrüssung fertig` aus. Das umgebaute Programm funktioniert dann auch in Aufgabe 1 noch, probier es aus.

```aufgabe raum=leer punkte=4
ziel: sitzt
ziel: ausgabe Begrüssung fertig
tipp: Vor jedes `lights`, `beep` und `pose` gehört eine Frage mit `spot.supports(...)`. Die Namen sind "lights", "beep" und "pose".
tipp: Du kannst auch einmal am Anfang fragen und dir die Antwort merken: `licht = spot.supports("lights")`.
---
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    spot.lights("blue", duration=1)
    for note in ["C", "E", "G"]:
        spot.beep(note, octave=5, duration=0.3)
    spot.pose(pitch=15)
    spot.pose()
    spot.lights("green", duration=1)
    spot.sit()
    print("Begrüssung fertig")
```
