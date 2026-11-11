---
nummer: 7
titel: Objekte finden
---

# AprilTags: Marken, die Spot erkennt

Ein **AprilTag** ist ein ausgedrucktes Quadrat mit einem schwarz-weissen Muster, ähnlich wie ein QR-Code. Jedes Muster steht für eine Nummer. Spots Kameras erkennen solche Tags und sagen dir, **welcher** es ist und **wo** er hängt. In der Schule kannst du so ein Ziel markieren: eine Tür, eine Ladestation, einen Schrank.

Im Raum «Möbliert» hängen zwei Tags: Tag 1 an der rechten Wand, Tag 2 an der oberen. Spot steht in der Mitte des Zimmers.

```spot raum=moebliert start=3.5,2.7,0
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    tags = spot.tags()
    print("Ich sehe", len(tags), "Tags.")
    for tag in tags:
        print(f"Tag {tag.id}: {tag.distance:.2f} m entfernt, Peilung {tag.bearing:+.1f}°")
```

`spot.tags()` gibt eine **Liste** zurück, für jeden sichtbaren Tag ein Eintrag. Jeder Eintrag weiss drei Dinge:

- `tag.id` ist die Nummer auf dem Tag.
- `tag.distance` ist der Abstand in Metern.
- `tag.bearing` ist die **Peilung**: in welcher Richtung der Tag liegt, in Grad, so wie bei `move(turn=...)`. 0 ist vorne, positiv ist links, negativ ist rechts.

Die Liste ist sortiert: **der nächste Tag kommt zuerst.** Sieht Spot gar keinen Tag, ist die Liste leer.

Suchst du einen bestimmten Tag, gibst du die Nummer mit: `spot.tags(id=1)` liefert nur Tag 1 (oder eine leere Liste).

```quiz punkte=2
? Spot soll zu Tag 1 gehen. Ein Schüler schreibt diesen Anfang. Was ist daran falsch, wenn Spot in der Mitte von «Möbliert» steht?
| tag = spot.tags()[0]
| spot.move(turn=tag.bearing)
A) Nichts, `[0]` ist immer der Tag mit der kleinsten Nummer.
B)* `[0]` ist der **nächste** Tag. Hier ist das Tag 2, also dreht sich Spot zum falschen Tag.
C) `tags()` gibt keine Liste zurück, `[0]` ist ein Fehler.
D) Spot dreht sich in die Gegenrichtung, weil die Peilung rechts positiv ist.
! Die Liste ist nach **Abstand** sortiert, nicht nach Nummer. Von der Mitte aus ist Tag 2 näher (1.26 m) als Tag 1 (2.50 m). Wer einen bestimmten Tag will, fragt `spot.tags(id=1)`. Und Achtung: Ist die Liste leer, gibt `[0]` einen Fehler. Darum prüft man vorher mit `if tags:`.
```

# Peilung und Abstand

Die Peilung ist **relativ zu Spot**, genau wie die Winkel bei `look().direction(...)` in Kapitel 6. Dreht sich Spot um die Peilung, schaut er also genau auf den Tag. Das Programm hier zeigt es: vorher liegt Tag 1 etwas rechts, nachher genau vorne.

```spot raum=moebliert start=3.5,2.7,0
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    tag = spot.tags(id=1)[0]
    print(f"Vorher: Peilung {tag.bearing:+.1f}°")
    spot.move(turn=tag.bearing)
    tag = spot.tags(id=1)[0]
    print(f"Nachher: Peilung {tag.bearing:+.1f}°")
```

Dann einfach so weit geradeaus gehen, wie der Tag entfernt ist? Probier es aus:

```spot raum=moebliert start=3.5,2.7,0 fehler=ja
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    tag = spot.tags(id=1)[0]
    spot.move(turn=tag.bearing)
    spot.move(forward=tag.distance)
    print("Angekommen!")
```

Spot stösst an die Wand. Der Tag **hängt an der Wand**, und Spots Mitte kann nicht in die Wand hinein. Wer zu einem Tag geht, muss vorher anhalten.

## Wo im Raum liegt der Tag?

Oft willst du nicht nur wissen, in welcher Richtung der Tag von Spot aus liegt, sondern **wo im Raum**. Dafür brauchst du Spots eigene Lage aus Kapitel 4:

- Die Richtung im Raum ist Spots Blick plus die Peilung: `z.heading + tag.bearing`.
- Von Spots Position aus gehst du in diese Richtung `tag.distance` weit. Das rechnen `cos` und `sin`.

```spot raum=moebliert start=3.5,2.7,0
import math
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    z = spot.state
    tag = spot.tags(id=1)[0]
    richtung = math.radians(z.heading + tag.bearing)
    tag_x = z.x + tag.distance * math.cos(richtung)
    tag_y = z.y + tag.distance * math.sin(richtung)
    print(f"Spot steht bei x = {z.x:.2f}, y = {z.y:.2f} und schaut nach {z.heading:.0f}°.")
    print(f"Tag 1 hängt bei x = {tag_x:.2f}, y = {tag_y:.2f}.")
```

Vergleiche mit der Karte: Tag 1 hängt tatsächlich bei x = 5.9, y = 2.

Der Vorteil: Diesen Punkt kannst du dir merken. Er bleibt gleich, auch wenn Spot weitergeht. Die Peilung dagegen ändert sich bei jedem Schritt.

```quiz punkte=2
? Spot steht bei x = 2, y = 1 und schaut nach oben (heading 90°). Er sieht einen Tag mit Peilung −90° in 1.5 m Abstand. Wo hängt der Tag?
A) Bei x = 2, y = 2.5
B)* Bei x = 3.5, y = 1
C) Bei x = 0.5, y = 1
D) Bei x = 2, y = −0.5
! Die Richtung im Raum ist 90° + (−90°) = **0°**, also nach rechts (Osten). Von x = 2 aus 1.5 m nach rechts ist x = 3.5, y bleibt 1. Wer nur die Peilung anschaut («−90°, also nach unten»), vergisst, dass Spot selbst nach oben schaut.
```

# Wenn Spot keinen Tag sieht

Spot hat fünf Kameras und sieht **rundherum**. Trotzdem findet er nicht jeden Tag:

- **Reichweite:** Im Simulator erkennt Spot einen Tag nur bis etwa **3 m** weit. Am echten Spot ist der Wert noch nicht gemessen, erwartet werden 2 bis 3 m. Ein Tag ist klein, von weit weg ist sein Muster nur ein paar Pixel gross.
- **Freie Sicht:** Steht etwas zwischen Spot und dem Tag, sieht er ihn nicht.

Hier steht Spot in der linken unteren Ecke. Er dreht sich einmal ganz im Kreis und schaut nach jedem Viertel:

```spot raum=moebliert start=1,1,0
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    for viertel in range(4):
        print("Blick", round(spot.state.heading), "°: Tags", [t.id for t in spot.tags()])
        spot.move(turn=90)
```

Kein einziger Tag, in keiner Richtung. Beide Tags sind mehr als 3 m entfernt. Drehen hilft nicht, weil Spot ohnehin rundum sieht. **Er muss näher heran.**

Also geht Spot in kleinen Schritten los und schaut nach jedem Schritt wieder. Dafür passt eine `while`-Schleife aus Kapitel 5:

```spot raum=moebliert start=1,0.6,0
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    schritte = 0
    while not spot.tags(id=1) and schritte < 10:
        spot.move(forward=0.5)
        schritte += 1
    if spot.tags(id=1):
        z = spot.state
        print(f"Tag 1 gefunden nach {schritte} Schritten, bei x = {z.x:.2f}.")
    else:
        print("Nach 10 Schritten noch kein Tag 1.")
```

`not spot.tags(id=1)` ist wahr, solange die Liste leer ist. Python behandelt eine leere Liste wie `False` und eine Liste mit Einträgen wie `True`. Das `schritte < 10` ist die Notbremse: Ohne sie liefe Spot bei einem verdeckten Tag immer weiter, bis er irgendwo anstösst.

```quiz punkte=2
? Spot steht 2 m vor Tag 4, aber ein Schrank steht genau dazwischen. `spot.tags()` ist leer. Was hilft?
A) Sich auf der Stelle einmal im Kreis drehen und dabei immer wieder `tags()` fragen.
B) `spot.tags(id=4)` statt `spot.tags()` schreiben.
C)* Seitlich am Schrank vorbeigehen, bis die Sicht frei ist, und dann wieder fragen.
D) Nichts, Tags hinter Hindernissen findet Spot nie.
! Spot sieht rundum, darum ändert Drehen nichts daran, was er sieht. Und `id=4` filtert nur die Liste, es macht keinen unsichtbaren Tag sichtbar. Der Schrank nimmt die **Sicht**: Erst von einem anderen Ort aus ist die Linie zum Tag frei. Suchen heisst bei Spot deshalb fast immer: **den Ort wechseln**.
```

# Aufgabe: Vor dem Tag anhalten

Spot soll im Raum «Möbliert» zu **Tag 1** gehen und davor anhalten, wie ein Hund, der vor der Tür sitzt:

- Er hält **0.6 bis 1.0 m vor dem Tag** an, gerade davor (nicht schräg daneben).
- Er schaut am Ende **zum Tag**.
- Er stösst nirgends an.

Du weisst nur: Tag 1 hängt an einer Wand, die nach **Westen** schaut. «Gerade davor» heisst also: gleiche Höhe y, etwa 0.8 m weiter links (kleineres x).

Dein Programm läuft von **vier Startplätzen** aus. Von dreien sieht Spot Tag 1 sofort. Vom vierten aus nicht: Dort muss er zuerst geradeaus gehen, bis er ihn sieht.

Ein Plan:

1. Solange Spot Tag 1 nicht sieht: 0.5 m geradeaus.
2. Rechne aus, wo im Raum Tag 1 hängt.
3. Geh mit `gehe_zu` zum Punkt 0.8 m vor dem Tag.
4. Dreh dich so, dass du zum Tag schaust (Osten, also heading 0°).

`gehe_zu` aus Kapitel 4 steht schon im Programm.

```aufgabe raum=moebliert punkte=6 starts=3.5,2.7,0;3.8,0.8,90;4.2,1,135;1,0.6,0
ziel: ende_in 4.9 1.7 5.4 2.3
ziel: blick 0 15
ziel: nicht_angestossen
ziel: ausgabe Vor Tag 1
tipp: Die Lage von Tag 1 im Raum: `richtung = math.radians(z.heading + tag.bearing)`, dann `tag_x = z.x + tag.distance * math.cos(richtung)` und dasselbe mit `sin` für `tag_y`. Lies `z = spot.state` und `tag` direkt nacheinander, damit beide zum selben Augenblick gehören.
tipp: Zum Schluss drehen: Die nötige Drehung ist `(0 - spot.state.heading + 180) % 360 - 180`. Das ist dieselbe Rechnung wie in `gehe_zu`, nur mit 0° als Ziel.
---
import math
from spotlab import connect

def gehe_zu(spot, x, y):
    z = spot.state
    dx = x - z.x
    dy = y - z.y
    richtung = math.degrees(math.atan2(dy, dx))
    drehung = (richtung - z.heading + 180) % 360 - 180
    spot.move(turn=drehung)
    spot.move(forward=math.hypot(dx, dy))

with connect() as spot:
    spot.power_on()
    spot.stand()

    # 1. Suchen, bis Tag 1 zu sehen ist

    # 2. Ausrechnen, wo Tag 1 hängt

    # 3. Zum Punkt 0.8 m vor dem Tag gehen

    # 4. Zum Tag drehen

    print("Vor Tag 1 angekommen.")
```
