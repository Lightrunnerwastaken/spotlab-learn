---
nummer: 4
titel: Wo ist Spot?
---

# Den Zustand lesen

Spot misst ständig, wo er ist und was er tut. Diese Messungen bekommst du mit `spot.state`, dem **Zustand**:

```spot raum=moebliert
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    zustand = spot.state
    print("x:", zustand.x, "m")
    print("y:", zustand.y, "m")
    print("Blick:", zustand.heading, "Grad")
    print("Tempo:", zustand.speed, "m/s")
    print("Akku:", zustand.battery, "%")
```

- `x` und `y` sind Spots Position in Metern.
- `heading` ist seine Blickrichtung in Grad: 0° heisst «schaut in Richtung grösserer x», 90° heisst «schaut in Richtung grösserer y». Der Wert liegt immer zwischen −180° und 180°.
- `speed` ist, wie schnell er gerade geht.

> Lies `spot.state` **einmal** in eine Variable und benutze dann die Variable. Jedes `spot.state` ist eine neue Messung. Wenn Spot sich gerade bewegt, gehören `spot.state.x` und ein späteres `spot.state.y` sonst zu zwei verschiedenen Zeitpunkten.

## Woher weiss Spot, wo er ist?

Spot zählt seine Schritte und misst, wie sich seine Beine bewegt haben. Daraus rechnet er aus, wie weit er gekommen ist. Das nennt man **Odometrie**. Der Startpunkt ist dort, wo Spot eingeschaltet wurde — im Simulator ist es der Startpunkt des Raums.

# Befohlen ist nicht gemessen

Führe dieses Programm aus und schau dir die Zahlen genau an:

```spot raum=moebliert
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    vorher = spot.state.x
    spot.move(forward=1.0)
    spot.move(turn=90)
    z = spot.state
    print("gegangen:", z.x - vorher, "m")
    print("Blick:", z.heading, "Grad")
    print("gerundet:", round(z.heading), "Grad")
```

Spot ist nicht genau 1 m gegangen und hat sich nicht genau um 90° gedreht. Er hält an, sobald er nahe genug am Ziel ist. Am echten Roboter sind die Abweichungen noch grösser: Er rutscht ein wenig, und die Odometrie irrt sich mit jedem Meter etwas mehr.

Für dich heisst das:

- Vergleiche Messungen nie mit `==`. `z.heading == 90` ist fast nie wahr. Frage stattdessen, ob der Wert **nahe genug** ist: `abs(z.heading - 90) < 5`.
- Mit `round(zahl, 2)` rundest du auf zwei Stellen nach dem Komma, damit die Ausgabe lesbar wird.

```quiz punkte=2
? Ein Programm soll prüfen, ob Spot nach links (90°) schaut. Welche Bedingung ist die beste?
A) `if spot.state.heading == 90:`
B) `if spot.state.heading > 90:`
C)* `if abs(spot.state.heading - 90) < 5:`
D) `if round(spot.state.heading) == 90:`
! Gemessene Werte sind nie ganz genau. `== 90` ist fast nie wahr. `round(...) == 90` klappt zwar bei 89.9, aber nicht mehr bei 89.4 — und das kann gut vorkommen. `abs(heading - 90) < 5` erlaubt bewusst eine Abweichung von 5° nach beiden Seiten.
```

# Rechnen mit der Position

Mit dem Zustand kann Spot ausrechnen, wie weit ein Ziel entfernt ist und in welcher Richtung es liegt. Dafür brauchst du die Bibliothek `math`:

- Der **Abstand** zwischen zwei Punkten: `math.hypot(dx, dy)` — das ist der Satz von Pythagoras, √(dx² + dy²).
- Die **Richtung** zu einem Punkt: `math.atan2(dy, dx)` gibt den Winkel in Radiant. `math.degrees(...)` macht Grad daraus.

```spot raum=moebliert
import math
from spotlab import connect

ziel_x, ziel_y = 4.5, 1.0

with connect() as spot:
    spot.power_on()
    spot.stand()
    z = spot.state
    dx = ziel_x - z.x
    dy = ziel_y - z.y
    print("Abstand zum Ziel:", round(math.hypot(dx, dy), 2), "m")
    print("Richtung zum Ziel:", round(math.degrees(math.atan2(dy, dx))), "Grad")
```

Ändere `ziel_x` und `ziel_y` und schau, was sich ändert. Was kommt heraus, wenn das Ziel genau über Spot liegt (gleiches x, grösseres y)?

## Wie weit muss Spot sich drehen?

Die Richtung zum Ziel ist ein Winkel **im Raum**. Spot dreht sich aber relativ zu seinem eigenen Blick. Die nötige Drehung ist also:

| drehung = richtung_zum_ziel - spot.state.heading

Dabei kann etwas Unschönes herauskommen: Schaut Spot nach 170° und das Ziel liegt bei −170°, ergibt die Rechnung −340°. Spot würde sich fast einmal ganz im Kreis drehen, obwohl 20° nach links reichen. Mit diesem Trick bringst du jeden Winkel zwischen −180° und 180°:

| drehung = (drehung + 180) % 360 - 180

```quiz punkte=2
? Spot schaut nach 170°. Das Ziel liegt in Richtung −170°. Welche Drehung ergibt `(drehung + 180) % 360 - 180` mit `drehung = -170 - 170`?
A) −340°
B) −20°
C)* 20°
D) 340°
! `drehung` ist −340. Dann: (−340 + 180) % 360 = (−160) % 360 = 200 (Python gibt bei `%` immer eine Zahl zwischen 0 und 359 zurück). 200 − 180 = **20**. Spot dreht also 20° nach links — der kurze Weg. Rechne es im Codefeld nach: `print((-340 + 180) % 360 - 180)`.
```

# Eine eigene Funktion: gehe_zu

Mit einer **Funktion** packst du mehrere Befehle unter einen Namen. Dann musst du sie nur einmal schreiben und kannst sie beliebig oft benutzen.

```spot raum=moebliert
from spotlab import connect

def quadrat(spot, seite):
    for i in range(4):          # viermal wiederholen
        spot.move(forward=seite)
        spot.move(turn=90)

with connect() as spot:
    spot.power_on()
    spot.stand()
    quadrat(spot, 1.0)
    print("Quadrat fertig")
```

`def quadrat(spot, seite):` legt die Funktion an. `spot` und `seite` sind ihre **Parameter**: Werte, die man ihr beim Aufruf mitgibt. Die eingerückten Zeilen darunter laufen erst, wenn jemand `quadrat(...)` aufruft.

`for i in range(4):` ist eine **Schleife**: die eingerückten Zeilen darunter laufen viermal.

# Aufgabe: Rundgang mit gehe_zu

Schreibe eine Funktion `gehe_zu(spot, x, y)`, die Spot zum Punkt (x, y) bringt — egal, wo er gerade steht und wohin er schaut. Benutze sie dann für einen Rundgang durch den leeren Raum: über die Punkte (3, 1), (3, 3) und (1, 3) zurück zum Start (1, 1).

```aufgabe raum=leer punkte=5
ziel: ende_bei 1.0 1.0 0.25
ziel: gefahren 7.5
ziel: nicht_angestossen
tipp: In gehe_zu: lies zuerst den Zustand, rechne dx und dy aus, dann die Richtung mit atan2 und die nötige Drehung. Danach drehen und `math.hypot(dx, dy)` weit vorwärts gehen.
tipp: Vergiss nicht, die Drehung mit `(drehung + 180) % 360 - 180` zwischen −180° und 180° zu bringen.
---
import math
from spotlab import connect

def gehe_zu(spot, x, y):
    z = spot.state
    # 1. dx und dy ausrechnen
    # 2. Richtung zum Ziel (in Grad) ausrechnen
    # 3. nötige Drehung ausrechnen und drehen
    # 4. vorwärts gehen
    pass

with connect() as spot:
    spot.power_on()
    spot.stand()
    for x, y in [(3, 1), (3, 3), (1, 3), (1, 1)]:
        gehe_zu(spot, x, y)
    print("Rundgang fertig")
```
