---
nummer: 13
titel: Treppen und Kanten
---

# Treppen erkennen

Spot kann Treppen steigen. Ein Schulhaus hat viele davon, und wer Spot von einem Stockwerk ins andere schicken will, muss wissen, wie das geht.

Zuerst muss Spot die Treppe **finden**. Dafür gibt es `spot.stairs()`. Es funktioniert wie `spot.tags()`: Du bekommst eine Liste, die nächste Treppe zuerst. Jede Treppe hat:

- `direction`: `"auf"`, wenn Spot unten (am Fuss) steht, `"ab"`, wenn er oben (am Kopf) steht
- `steps`: Anzahl Stufen
- `rise_m`: wie hoch die Treppe insgesamt ist, in Metern
- `distance`, `bearing`: Abstand und Peilung zur nächsten Kante der Treppe
- `axis_bearing`: in welcher Richtung es **bergauf** geht, als Peilung von Spot aus (links positiv)

Der Raum «Treppe» hat unten ein Zimmer, eine Treppe mit 7 Stufen und oben ein Podest. Auf der Karte ist die Treppe die hellblaue Fläche in der Mitte, das Podest die rechts davon.

```spot raum=treppe
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    print("Treppen erkennen:", spot.supports("stairs"))
    print(f"Körperhöhe: {spot.state.z:.2f} m")
    for t in spot.stairs():
        print(f"Treppe {t.direction}: {t.steps} Stufen, {t.rise_m:.2f} m hoch")
        print(f"  {t.distance:.2f} m entfernt, Peilung {t.bearing:.0f}°, bergauf bei {t.axis_bearing:.0f}°")
```

`spot.state.z` ist die Höhe von Spots Körper. Unten sind es 0.51 m, denn so hoch steht Spot über dem Boden. Steigt `z`, ist Spot nach oben gekommen.

```quiz punkte=2
? Spot steht unten vor der Treppe und schaut nach links weg. `stairs()` meldet `axis_bearing = -90`. Was musst du tun, damit Spot die Treppe hinaufschaut?
A) `spot.move(turn=90)`
B)* `spot.move(turn=-90)`
C) `spot.move(turn=180)`
D) Nichts, Spot dreht sich beim Gehen von selbst zur Treppe.
! `axis_bearing` ist eine Peilung wie bei einem Tag: −90° heisst «bergauf liegt 90° rechts von mir». `move(turn=…)` dreht um genau diesen Winkel, also stellt `spot.move(turn=t.axis_bearing)` die Nase immer bergauf, egal wie Spot vorher stand.
```

# Treppen steigen

Für Treppen gibt es in spotlab eine feste Regel, nach der Vorgabe von Boston Dynamics, der Firma, die Spot baut:

> **Auf einer Treppe zeigt die Nase immer bergauf.** Hinauf geht Spot vorwärts, hinunter geht er **rückwärts**, ohne sich umzudrehen.

Das Hinaufgehen sieht so aus: Nase bergauf drehen, dann vorwärts gehen, bis der Körper um die Höhe der Treppe gestiegen ist. Gemächlich, mit 0.25 m/s:

```spot raum=treppe
import time
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    t = spot.stairs()[0]
    unten = spot.state.z
    spot.move(turn=t.axis_bearing)              # Nase bergauf
    while spot.state.z - unten < t.rise_m - 0.05:
        spot.walk(vx=0.25, duration=1.0, stop=False)
        time.sleep(0.2)
    spot.walk(vx=0.25, duration=1.5)            # noch ein Stück aufs Podest
    print(f"Oben: Körperhöhe {spot.state.z:.2f} m")
    for tag in spot.tags():
        print(f"Tag {tag.id} in {tag.distance:.1f} m")
```

Oben ist der Körper 1.71 m hoch, genau 1.20 m höher als unten. Und jetzt sieht Spot Tag 3, der oben an der Wand hängt.

Was passiert, wenn Spot oben umdreht und **vorwärts** hinuntergehen will? Häng diese drei Zeilen an das Programm an (innerhalb von `with`):

```python
    spot.move(turn=180)
    spot.walk(vx=0.3, duration=4)
    print(f"Körperhöhe {spot.state.z:.2f} m")
```

Spot bleibt an der Treppenkante stehen, die Körperhöhe bleibt 1.71 m. spotlab verweigert den Schritt und schreibt in die Aufzeichnung, wie herum es gehen würde. Der Kurs zeigt diese Meldung unter der Ausgabe an.

```quiz punkte=2
? Spot ist oben auf dem Podest ein paar Schritte gegangen und schaut jetzt **von der Treppe weg**, die Treppe liegt direkt hinter ihm. Wie kommt er nach unten?
A) Umdrehen und vorwärts hinuntergehen.
B)* Einfach rückwärts gehen, ohne sich zu drehen.
C) Um 90° drehen und seitwärts hinuntergehen.
D) Gar nicht, Spot kann nur hinauf.
! Wenn die Treppe hinter Spot liegt, zeigt seine Nase schon bergauf, denn bergauf ist dort, wo das Podest ist. Rückwärts gehen heisst dann rückwärts hinunter, genau so, wie es die Regel will. Ein Umdrehen wäre hier falsch, denn danach zeigte die Nase bergab.
```

Jetzt du: Spot geht die Treppe hinauf, meldet oben, welchen Tag er sieht, kommt **rückwärts** wieder herunter und setzt sich unten hin. Das Programm läuft von drei Startplätzen aus, und Spot schaut dort jedes Mal in eine andere Richtung.

```aufgabe raum=treppe punkte=6 starts=1,2,0;1,2,90;0.7,1.5,180
ziel: ausgabe Tag 3
ziel: ende_in 0 0 2.4 4
ziel: treppe_richtig
ziel: nicht_angestossen
ziel: sitzt
tipp: Oben gibt `spot.tags()` eine Liste. Gib den ersten Eintrag aus, zum Beispiel mit `print(f"Tag {tags[0].id}")`.
tipp: Rückwärts heisst `vx` negativ: `spot.walk(vx=-0.25, duration=1.0, stop=False)`. Geh so lange, bis die Körperhöhe wieder bei `unten` ist (`spot.state.z - unten > 0.05`).
tipp: Ganz unten noch ein Stück weiter rückwärts gehen (`spot.walk(vx=-0.25, duration=1.0)`), damit Spot nicht auf der untersten Stufe stehen bleibt, und dann `spot.sit()`.
---
import time
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    t = spot.stairs()[0]
    unten = spot.state.z
    spot.move(turn=t.axis_bearing)              # Nase bergauf
    while spot.state.z - unten < t.rise_m - 0.05:
        spot.walk(vx=0.25, duration=1.0, stop=False)
        time.sleep(0.2)
    spot.walk(vx=0.25, duration=1.5)

    # oben: welchen Tag siehst du?

    # rückwärts hinunter, bis die Körperhöhe wieder unten ist

    # hinsetzen
```

# Kanten

Das Podest ist 1.20 m hoch. Was passiert an seinem Rand, dort, wo keine Treppe ist? In diesem Programm geht Spot hinauf, weiter aufs Podest, dann nach rechts und schliesslich auf den Rand zu:

```spot raum=treppe
import time
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    t = spot.stairs()[0]
    unten = spot.state.z
    spot.move(turn=t.axis_bearing)
    while spot.state.z - unten < t.rise_m - 0.05:
        spot.walk(vx=0.25, duration=1.0, stop=False)
        time.sleep(0.2)
    spot.walk(vx=0.25, duration=1.5)
    spot.move(forward=0.6)
    spot.move(turn=-90)
    spot.move(forward=1.5)
    spot.move(turn=-90)                         # jetzt schaut er auf den Rand
    blick = spot.look(max_distance=1.0, start=0.6, margin=0.35)
    print("Vorne:", blick.front.status)
    spot.walk(vx=0.3, duration=4)
    print(f"x = {spot.state.x:.2f}, Körperhöhe {spot.state.z:.2f} m")
```

`look()` meldet vorne `blocked`, obwohl dort keine Wand steht. Und als Spot trotzdem losgeht, bleibt er am Rand stehen (der rote Kreis auf der Karte), und die Körperhöhe bleibt 1.71 m. Für spotlab ist eine **Kante** ein Hindernis wie eine Wand. Das Hindernisgitter aus Kapitel 6 ist nämlich eine Karte des **Bodens**: Es meldet nicht nur Dinge, die im Weg stehen, sondern auch Stellen, an denen der Boden zu weit hinauf- oder hinuntergeht.

Wie weit ist «zu weit»? In spotlab ist ein Höhensprung über **0.25 m** ein Hindernis. Kleinere Stufen geht Spot einfach, so wie du über einen Bordstein steigst.

```quiz punkte=2
? Spot geht im Übungsraum über drei Stellen: eine Türschwelle (3 cm), eine Rampe, die langsam um 40 cm ansteigt, und eine Kante, an der der Boden um 40 cm abfällt. Welche davon meldet das Hindernisgitter als Hindernis?
A) Alle drei.
B) Nur die Türschwelle.
C)* Nur die Kante.
D) Die Rampe und die Kante, beide sind 40 cm.
! Gezählt wird der **Sprung** von einer Stelle zur nächsten, nicht die Höhe insgesamt. Die Schwelle springt nur 3 cm, die Rampe steigt in vielen kleinen Stücken an, und beide sind darum begehbar. Nur an der Kante springt der Boden auf einmal um 40 cm, mehr als 0.25 m, also ist dort ein Hindernis. Genau so ist auch die Treppe kein Hindernis: Jede Stufe ist nur gut 17 cm hoch.
```

# Am echten Spot

Am echten Spot erkennt Spot die Treppen selbst, mit seinen Kameras. Ob er sie benutzen darf, steht in spotlabs Einstellungen (`config.toml`, Abschnitt `[limits]`):

| treppen = "auto"      # Spot erkennt Treppen und geht sie (Vorgabe)
| treppen = "aus"       # Spot behandelt Treppen wie Kanten und meidet sie

`treppen` ist ein **Sicherheitswert**. spotlab schickt ihn bei jedem Fahrbefehl mit, auch bei `walk()` und `move()`. Wer verhindern will, dass ein Programm Spot aus Versehen eine Treppe hinunterschickt, stellt `"aus"` ein. Im Übungsraum gilt dieselbe Einstellung: Mit `"aus"` werden Treppen und Rampen zu Kanten.

Zwei Dinge sind am echten Spot anders als im Übungsraum:

- **Die Regel «Nase bergauf» ist im Übungsraum streng.** Was der echte Spot tut, wenn ein Programm ihn vorwärts auf eine Treppe hinunterschickt, ist in spotlab noch nicht am Gerät geprüft. Darum: Schreib deine Programme so, dass sie die Regel einhalten, dann laufen sie überall.
- **Treppen sind gefährlich.** Ein Sturz auf einer Treppe kann Spot schwer beschädigen. Treppen nur mit Aufsicht, gemächlichem Tempo und dem Tablet mit Not-Aus in der Hand. Und nie, wenn unten jemand steht.

```quiz punkte=2
? Deine Klasse lässt Spot im zweiten Stock durch einen Gang laufen, an dessen Ende eine Treppe nach unten führt. Das Programm soll nur im Gang erkunden. Was ist die sicherste Einstellung?
A) `treppen = "auto"`, das Programm wird die Treppe schon nicht finden.
B)* `treppen = "aus"`: Dann behandelt Spot die Treppe wie eine Kante und geht nicht hinunter, auch wenn das Programm einen Fehler hat.
C) Das Tempo auf 0.1 m/s stellen.
D) Am Ende des Gangs ein Tag aufhängen.
! Eine Sicherheitsregel gehört in die Einstellungen, nicht in die Hoffnung, dass das Programm keinen Fehler hat. Mit `"aus"` meidet Spot jede Treppe, egal was der Code befiehlt. Das ist dieselbe Idee wie der Tempodeckel in spotlab: Er gilt für jedes Programm, auch für eines, das zu schnell sein will.
```
