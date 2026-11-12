---
nummer: 3
titel: Spot bewegen
---

# Eine Strecke gehen: move

Mit `spot.move()` geht Spot eine feste Strecke. Die Strecke gibst du in **Metern** an.

```spot raum=moebliert
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    spot.move(forward=1.5)    # 1.5 m nach vorne
    print("angekommen")
```

Rechts siehst du jetzt eine türkise Spur: so ist Spot gegangen. Unter der Karte steht, wo er gerade ist: `x` und `y` in Metern, und der **Blick** in Grad.

> Achte auf den Punkt statt dem Komma: In Python schreibt man `1.5`, nicht `1,5`. Ein Komma trennt in Python zwei Werte voneinander.

Mit einer negativen Zahl geht Spot rückwärts: `spot.move(forward=-0.5)`. Am echten Spot ist das heikel, denn nach hinten sieht er schlecht. Geh rückwärts nur kurze Stücke.

# Drehen

`move` kann Spot auch drehen. Die Drehung gibst du in **Grad** an:

- `spot.move(turn=90)` dreht Spot um 90° nach **links** (gegen den Uhrzeigersinn).
- `spot.move(turn=-90)` dreht ihn um 90° nach **rechts**.

```spot raum=moebliert
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    spot.move(forward=1.0)
    spot.move(turn=90)        # Vierteldrehung nach links
    spot.move(forward=1.0)
```

Wichtig: **«vorne» ist immer dort, wohin Spot gerade schaut.** Nach der Drehung zeigt `forward` in eine andere Richtung als vorher. Man sagt: die Befehle gelten im **Körperrahmen** von Spot, nicht im Raum.

```quiz punkte=2
? Spot steht bei x = 1, y = 1 und schaut nach rechts (in Richtung grösserer x-Werte). Er bekommt diese Befehle. Wo steht er danach?
| spot.move(forward=1)
| spot.move(turn=90)
| spot.move(forward=1)
| spot.move(turn=90)
| spot.move(forward=1)
A) x = 4, y = 1
B)* x = 1, y = 2
C) x = 3, y = 2
D) x = 1, y = 0
! Zeichne es auf: Nach 1 m nach rechts steht Spot bei (2, 1). Die Linksdrehung lässt ihn nach oben schauen, 1 m bringt ihn zu (2, 2). Die zweite Linksdrehung lässt ihn nach links schauen, also Richtung kleinerer x-Werte: 1 m bringt ihn zu **(1, 2)**. Wer A wählt, hat vergessen, dass «vorne» mit Spot mitdreht; wer D wählt, hat nach rechts gedreht. Prüfe es nach, indem du die Befehle im Codefeld oben ausführst.
```

# Seitwärts gehen

Spot kann auch seitwärts gehen, ohne sich zu drehen: mit `left`. Positive Werte gehen nach links, negative nach rechts.

```spot raum=moebliert
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    spot.move(left=1.0)                # 1 m nach links, Blick bleibt gleich
    spot.move(forward=1.0, left=-0.5)  # schräg: vor und nach rechts zugleich
```

Du kannst `forward`, `left` und `turn` in einem Befehl kombinieren. Für den Anfang ist es aber übersichtlicher, einen Befehl nach dem anderen zu geben.

```quiz punkte=1
? Spot soll einen Schritt nach rechts machen, ohne sich zu drehen. Welcher Befehl ist richtig?
A) `spot.move(right=0.5)`
B) `spot.move(turn=-90)`
C)* `spot.move(left=-0.5)`
D) `spot.move(forward=-0.5)`
! Einen Befehl `right` gibt es nicht. Rechts ist einfach «negativ links». `turn=-90` würde Spot drehen und `forward=-0.5` geht rückwärts.
```

# Mit Tempo gehen: walk

Neben `move` gibt es `spot.walk()`. Statt einer Strecke gibst du eine **Geschwindigkeit** und eine **Dauer** an:

- `vx`: vorwärts, in Metern pro Sekunde (m/s)
- `vy`: nach links, in m/s
- `wz`: Drehung nach links, in **Radiant pro Sekunde** (rad/s)
- `duration`: wie viele Sekunden lang

```spot raum=moebliert
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    spot.walk(vx=0.5, duration=2)     # 2 Sekunden lang mit 0.5 m/s
    print("x ist jetzt", spot.state.x)
```

Rechne nach: 0.5 m/s mal 2 s ergibt 1 m. Spot ist aber weniger weit gekommen. Warum? Er braucht zuerst ein bisschen Zeit, um auf Tempo zu kommen, und bremst am Schluss. Bei `move` rechnet spotlab das selbst aus, bei `walk` nicht.

## Radiant statt Grad

Bei `walk` wird die Drehung nicht in Grad gemessen, sondern in **Radiant**. Ein ganzer Kreis sind 360° oder 2π ≈ 6.28 Radiant. Ein Radiant ist also ungefähr 57°.

> Wann nimmt man was? `move` ist gut, wenn du weisst, **wohin** Spot soll. `walk` ist gut, wenn Spot immer wieder neu entscheidet, zum Beispiel in einer Schleife, die jede halbe Sekunde schaut, ob etwas im Weg ist.

```quiz punkte=2
? Spot dreht sich mit `spot.walk(wz=0.5, duration=2)`. Um ungefähr wie viel dreht er sich (wenn man das Anlaufen nicht beachtet), und in welche Richtung?
A) 1° nach links
B) 1° nach rechts
C)* 57° nach links
D) 90° nach links
! 0.5 rad/s mal 2 s ergibt 1 Radiant, und 1 Radiant sind ungefähr 57°. Positives `wz` dreht nach links, genau wie `turn` bei `move`. Im Simulator kommt Spot wegen des Anlaufens auf etwas weniger. Probiere es aus!
```

# Aufgabe: Einparken

Im Raum «Möbliert» steht ein Tisch und zwei Stuhlstapel. Parke Spot in der Lücke **zwischen dem Tisch und den Stuhlstapeln**, bei x = 3.1 und y = 2.55. Er soll dabei nach **links** schauen (180°) und nirgends anstossen.

Der direkte Weg führt durch den Tisch. Plane den Weg zuerst auf Papier!

```aufgabe raum=moebliert punkte=4
ziel: ende_bei 3.1 2.55 0.3
ziel: blick 180 15
ziel: nicht_angestossen
tipp: Gehe zuerst auf der Karte unterhalb des Tisches (bei kleinerem y) nach rechts, bis du rechts vom Tisch bist. Der Tisch reicht von x = 2.5 bis x = 3.7.
tipp: Ein möglicher Weg: 3.2 m vor, links drehen, 1.55 m vor, nochmals links drehen, den Rest vor.
---
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    # Dein Weg zur Lücke:
```
