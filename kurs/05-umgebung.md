---
nummer: 5
titel: Umgebung wahrnehmen
---

# Was sieht Spot?

Bis jetzt ist Spot blind gelaufen: Du hast ihm gesagt, wie weit er gehen soll, und gehofft, dass nichts im Weg steht. Spot hat aber fünf Tiefenkameras rundherum. Daraus baut er sich eine Karte der Hindernisse um sich herum.

Mit `spot.look()` fragst du diese Karte in vier Richtungen ab: vorne, links, rechts und hinten.

```spot raum=moebliert
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    blick = spot.look(start=0.6)
    for richtung in ("front", "left", "right", "back"):
        strahl = getattr(blick, richtung)
        print(richtung, strahl.status, strahl.distance)
```

Für jede Richtung bekommst du einen **Status**:

- `clear` — frei, so weit Spot nachschaut (normal 1.8 m).
- `blocked` — da ist etwas. `distance` sagt, wie weit der Weg frei ist (in Metern ab Spots Mitte). Achtung: `look` hält einen Sicherheitsabstand von 0.3 m ein. Steht eine Wand 1 m vor Spot, meldet `distance` darum etwa 0.7, nicht 1.0.
- `unknown` — Spot weiss es nicht. Zum Beispiel, weil er dort nichts sieht.

Was bedeutet das `start=0.6`? Das erklärt der nächste Abschnitt.

# Der blinde Fleck unter dem Bauch

Lass im Codefeld oben das `start=0.6` weg (also nur `spot.look()`) und führe es nochmals aus.

Jetzt ist alles `unknown`. Das ist kein Fehler: Direkt unter und neben seinem Körper sieht Spot nichts, seine Kameras schauen nach aussen. `look()` prüft jede Richtung **von der Mitte aus**, und weil die ersten Zentimeter unbekannt sind, kann es nichts Sicheres sagen.

Mit `start=0.6` sagst du: «Fang erst 0.6 m von der Mitte an zu prüfen.» Das ist ungefähr dort, wo Spots Körper aufhört.

> **Achtung:** Was im blinden Fleck steht, sieht Spot nicht — auch am echten Roboter nicht. Ein Hindernis, das näher als etwa 0.5 m ist, kann `look` übersehen. Darum lässt man Spot nie direkt an ein Hindernis heranlaufen.

```quiz punkte=2
? `spot.look(start=0.6).front` meldet `clear` mit `distance` 1.8. Was weisst du sicher?
A) Vor Spot ist bis zur nächsten Wand alles frei.
B)* Zwischen 0.6 m und 1.8 m vor Spots Mitte hat Spot kein Hindernis gesehen.
C) Spot kann jetzt gefahrlos 1.8 m vorwärts gehen.
D) Vor Spot ist bis 0.6 m alles frei.
! `clear` sagt nur etwas über den Abschnitt, den `look` geprüft hat: ab `start` bis `max_distance`. Über das Stück davor (den blinden Fleck) und alles nach 1.8 m sagt es nichts. Auch C stimmt nicht ganz: Spot ist breiter als der Strahl, den `look` prüft — und am echten Roboter kann sich in der Zwischenzeit etwas bewegen.
```

# Gehen, bis etwas im Weg ist

Jetzt kommt alles zusammen. Mit einer `while`-Schleife wiederholt Spot etwas, **solange** eine Bedingung gilt:

```spot raum=leer start=0.5,2.5,0
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    while spot.look(max_distance=1.0, start=0.6).front.status == "clear":
        spot.move(forward=0.25)
        print("Schritt, x =", round(spot.state.x, 2))
    print("Da ist etwas! Ich bleibe stehen.")
```

Bei jedem Durchgang schaut Spot nach vorne. Ist es auf dem nächsten Meter frei, geht er 25 cm weiter. Sobald etwas im Weg ist, endet die Schleife.

Spot weiss dabei **nicht**, wie weit die Wand weg ist. Er findet es heraus, während er geht. Genau so funktionieren Programme für unbekannte Räume.

```quiz punkte=2
? Jemand ändert die Schleife oben so, dass Spot mit `spot.move(forward=1.5)` geht statt mit 0.25. Was kann passieren?
A) Nichts, Spot bleibt trotzdem vor der Wand stehen.
B) Spot wird schneller fertig und bleibt näher an der Wand stehen, sonst ändert sich nichts.
C)* Spot kann an die Wand stossen: Er schaut nur 1 m weit, geht dann aber 1.5 m, ohne dazwischen nochmals nachzuschauen.
D) Python meldet einen Fehler, weil 1.5 grösser ist als max_distance.
! Während `move` läuft, schaut dein Programm nicht hin. Darum muss jeder Schritt **kürzer** sein als die Strecke, die du vorher als frei geprüft hast. Probiere es aus: Mit 1.5 läuft Spot auf der Karte gegen die Wand (roter Kreis).
```

# Aufgabe: Bis kurz vor die Wand

Spot steht diesmal an einer anderen Stelle im leeren Raum. Er soll geradeaus gehen, bis er kurz vor der Wand steht — **ohne anzustossen** und ohne dass du ihm sagst, wie weit die Wand weg ist. Am Ende soll er «Wand erreicht» ausgeben.

```aufgabe raum=leer start=0.6,1.5,0 punkte=4
ziel: ende_bei 4.0 1.5 0.5
ziel: nicht_angestossen
ziel: ausgabe Wand erreicht
ziel: aufgerufen move
ziel: aufgerufen look
tipp: Benutze eine `while`-Schleife mit `spot.look(max_distance=1.0, start=0.6)`, wie im Abschnitt vorher.
tipp: Bleibt Spot zu früh stehen? Dann ist `max_distance` zu gross. Stösst er an? Dann sind die Schritte zu lang.
---
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    # Geh vorwärts, solange vorne frei ist ...
```
