---
nummer: 11
titel: Karten und Navigation
---

# Eine eigene Karte aufnehmen

In Kapitel 8 hat sich Spot gemerkt, **wo er war**. Jetzt merkt er sich auch, **was er gesehen hat**, und daraus entsteht eine Karte.

Die Idee: `look()` liefert bei jedem Schritt das Hindernisgitter rund um Spot mit (`blick.grid`, Kapitel 6). Es reicht nur knapp 2 m weit, aber Spot geht ja herum. Wenn er bei jedem Schritt einträgt, was er gerade sieht, wächst die Karte Stück für Stück.

Die Karte ist wieder ein Dictionary, diesmal mit Feldern von 25 cm. Jedes Feld bekommt `"#"` (Hindernis) oder `"."` (frei). Felder, die Spot nie gesehen hat, fehlen einfach. Die Funktion `eintragen` geht alle Felder in Spots Umgebung durch und fragt das Gitter:

```spot raum=wohnung start=1,1,90
import math
from spotlab import connect

ZELLE = 0.25
karte = {}          # (spalte, reihe) -> "#" oder "."
besuche = {}

def feld(x, y):
    return (int(x // 0.5), int(y // 0.5))

def eintragen(blick):
    gitter = blick.grid
    sx, sy = blick.position[0], blick.position[1]
    for i in range(int((sx - 1.8) // ZELLE), int((sx + 1.8) // ZELLE) + 1):
        for j in range(int((sy - 1.8) // ZELLE), int((sy + 1.8) // ZELLE) + 1):
            x, y = (i + 0.5) * ZELLE, (j + 0.5) * ZELLE      # Mitte des Feldes
            d = gitter.distance_at(x, y)
            if d is None:
                continue                                     # nicht gesehen
            karte[(i, j)] = "#" if d < ZELLE / 2 else "."

with connect() as spot:
    spot.power_on()
    spot.stand()
    for schritt in range(50):
        z = spot.state
        besuche[feld(z.x, z.y)] = besuche.get(feld(z.x, z.y), 0) + 1
        blick = spot.look(max_distance=1.0, start=0.6, margin=0.35)
        eintragen(blick)
        # Erkunden wie in Kapitel 8
        bester_winkel, beste_zahl = None, None
        for winkel in sorted(range(-180, 180, 15), key=abs):
            if blick.direction(winkel).status != "clear":
                continue
            r = math.radians(z.heading + winkel)
            zahl = besuche.get(feld(z.x + math.cos(r), z.y + math.sin(r)), 0)
            if beste_zahl is None or zahl < beste_zahl:
                bester_winkel, beste_zahl = winkel, zahl
        if bester_winkel is None:
            spot.move(turn=90)
        else:
            spot.move(turn=bester_winkel)
            spot.move(forward=0.5)

    z = spot.state
    for j in range(19, -1, -1):              # oben ist y = 5 m
        zeile = ""
        for i in range(32):                  # links ist x = 0
            if (i, j) == (int(z.x // ZELLE), int(z.y // ZELLE)):
                zeile += "S"                 # hier steht Spot jetzt
            else:
                zeile += karte.get((i, j), " ")
        print(zeile)
```

Vergleiche die Karte in der Ausgabe mit dem Grundriss. Nach 50 Schritten sind alle Wände da, beide Türen, der Schrank, das Sofa und die Kiste. Und das alles nur aus dem, was Spot unterwegs gesehen hat.

Warum steht im Gitter eine Distanz und nicht einfach «Wand ja/nein»? `distance_at(x, y)` sagt, wie weit es von diesem Punkt bis zum nächsten Hindernis ist. Ist das weniger als eine halbe Zelle, liegt das Hindernis im Feld selbst, also `"#"`.

> Im Übungsraum weiss Spot genau, wo er steht. Ein echter Roboter weiss das nie ganz genau: Seine Schritte rutschen, und nach 50 m kann er sich um einen halben Meter verschätzt haben. Dann landet dieselbe Wand zweimal auf der Karte, leicht versetzt. Wie Spot dieses Problem löst, kommt im letzten Abschnitt.

```quiz punkte=2
? Ein Schüler ändert in `eintragen` die Zeile `if d is None: continue` zu `if d is None: karte[(i, j)] = "."`. Was passiert?
A) Nichts Wichtiges, die Karte wird nur etwas voller.
B)* Alles, was Spot nicht gesehen hat, steht als «frei» auf der Karte, zum Beispiel der Bereich hinter einer Wand. Wer später mit dieser Karte plant, plant durch Wände hindurch.
C) Die Karte bekommt mehr Wände, weil unbekannte Felder als Hindernis zählen.
D) Das Programm stürzt ab, weil man `None` nicht vergleichen kann.
! `None` heisst «keine Messung», und hinter jeder Wand gibt es keine Messung. Wer das als frei einträgt, bekommt eine Karte, die überall dort lügt, wo Spot nicht hingesehen hat. Das ist dieselbe Regel wie in Kapitel 10: Nichts gesehen ist nicht dasselbe wie frei. Auf einer guten Karte gibt es darum **drei** Arten von Feldern: frei, Hindernis, unbekannt.
```

# Wegpunkte: Orte merken

Eine Karte mit Wänden ist schön zum Anschauen. Um **zurückzufinden**, braucht Spot etwas Einfacheres: eine Liste der Orte, an denen er war, in der richtigen Reihenfolge. So eine Liste heisst **Wegpunkte**.

Beim Erkunden hängt Spot nach jedem Schritt seine Position an:

```python
wegpunkte = []
...
spot.move(turn=bester_winkel)
spot.move(forward=0.5)
z = spot.state
wegpunkte.append((z.x, z.y))
```

Zwischen zwei Wegpunkten liegt immer genau ein gerader Schritt von 0.5 m, den Spot schon einmal gegangen ist, ohne anzustossen. Die Liste ist also mehr als eine Sammlung von Orten. Sie ist ein **Weg, von dem man weiss, dass er geht**.

```quiz punkte=2
? Spot hat Tag 5 gefunden und will zurück zum Start. Ein Schüler schlägt vor: «Einfach `gehe_zu(spot, start_x, start_y)`, das ist der kürzeste Weg.» Was spricht dagegen?
A) Nichts, das ist die beste Lösung.
B) `gehe_zu` funktioniert nur für Wege unter 1 m.
C)* Die gerade Linie zum Start kann durch Wände führen. Spot weiss nur von seinen Wegpunkten sicher, dass man dort gehen kann.
D) Spot weiss nicht mehr, wo der Start liegt.
! Vom Ort, an dem Spot Tag 5 sieht, führt die gerade Linie zum Start mitten durch die Wand zwischen den Zimmern (im Kurs nachgeprüft: Spot stösst an). Der Weg über die Wegpunkte ist länger, aber jeder Abschnitt davon ist schon einmal gegangen worden. Genau so plant Spots eigene Navigation: Sie fährt nur auf Wegen, die bei der Aufnahme gegangen wurden.
```

# Den Weg zurück

Jetzt baust du es zusammen: Spot erkundet die Wohnung, bis er Tag 5 sieht, und geht dann über seine Wegpunkte **zurück zum Start**. Dafür gehst du die Liste rückwärts durch, `reversed(wegpunkte)`, und gehst mit `gehe_zu` von Wegpunkt zu Wegpunkt.

Dein Programm läuft von drei Startplätzen aus. Jedes Mal muss Spot genau dort enden, wo er losgegangen ist.

```aufgabe raum=wohnung punkte=8 starts=1,1,90;7,4,180;1,4.5,-90
ziel: ausgabe Tag 5 gesehen
ziel: zurueck 0.3
ziel: nicht_angestossen
tipp: Den Startplatz als ersten Wegpunkt nicht vergessen: gleich nach `spot.stand()` einmal `wegpunkte.append((z.x, z.y))`.
tipp: Hänge einen Wegpunkt nur an, wenn Spot wirklich gegangen ist (nach `move(forward=0.5)`), nicht nach einem reinen Drehen.
tipp: Der Rückweg ist eine einzige Schleife: `for x, y in reversed(wegpunkte): gehe_zu(spot, x, y)`.
---
import math
from spotlab import connect

def feld(x, y):
    return (int(x // 0.5), int(y // 0.5))

def gehe_zu(spot, x, y):
    z = spot.state
    dx, dy = x - z.x, y - z.y
    if math.hypot(dx, dy) < 0.05:
        return                                  # schon da
    richtung = math.degrees(math.atan2(dy, dx))
    spot.move(turn=(richtung - z.heading + 180) % 360 - 180)
    spot.move(forward=math.hypot(dx, dy))

besuche = {}
wegpunkte = []

with connect() as spot:
    spot.power_on()
    spot.stand()
    # Startplatz als ersten Wegpunkt merken

    for schritt in range(80):
        if spot.tags(id=5):
            print("Tag 5 gesehen")
            break
        z = spot.state
        besuche[feld(z.x, z.y)] = besuche.get(feld(z.x, z.y), 0) + 1
        blick = spot.look(max_distance=1.0, start=0.6, margin=0.35)
        bester_winkel, beste_zahl = None, None
        for winkel in sorted(range(-180, 180, 15), key=abs):
            if blick.direction(winkel).status != "clear":
                continue
            r = math.radians(z.heading + winkel)
            zahl = besuche.get(feld(z.x + math.cos(r), z.y + math.sin(r)), 0)
            if beste_zahl is None or zahl < beste_zahl:
                bester_winkel, beste_zahl = winkel, zahl
        if bester_winkel is None:
            spot.move(turn=90)
        else:
            spot.move(turn=bester_winkel)
            spot.move(forward=0.5)
            # Wegpunkt merken

    # Über die Wegpunkte zurück zum Start
```

Wenn es läuft, schau dir die Wege auf der Karte an. Spot geht manchmal Umwege zurück, weil er beim Erkunden Schleifen gelaufen ist und sie jetzt rückwärts noch einmal läuft. **Eine Idee für dich:** Bevor Spot losgeht, kürze die Liste. Wenn ein Wegpunkt sehr nahe (unter 0.3 m) bei einem viel späteren liegt, kann man alles dazwischen weglassen. So wird aus der Kette ein kürzerer Weg, ohne dass er unsicherer wird.

# GraphNav am echten Spot

Was du in diesem Kapitel gebaut hast, kann Spot von Haus aus, nur gründlicher. Es heisst **GraphNav**, und spotlab macht es dir zugänglich. Es läuft nur am echten Spot. Im Übungsraum gibt es kein GraphNav:

```spot raum=leer
from spotlab import connect

with connect() as spot:
    print("navigate_to im Übungsraum:", spot.supports("navigate_to"))
```

So läuft es am echten Spot:

**1. Aufnehmen.** In spotlab, Reiter «Karten»: «Aufnahme starten», dann Spot durch das Gebäude führen, zum Beispiel mit dem Tablet oder im Reiter «Fahren». Zum Start muss Spot einen **AprilTag** sehen, sonst beginnt die Aufnahme nicht. Unterwegs legt Spot selbst Wegpunkte an, ungefähr wie deine Liste, nur mit mehr Wissen pro Punkt: Er merkt sich auch, was er dort gesehen hat. Wichtige Orte bekommen im Reiter «Karten» einen Namen («Bibliothek», «Ladestation»).

**2. Verbessern.** Beim Speichern rechnet Spot die Karte nach. Das Wichtigste heisst **Schleifenschluss**: Wenn Spot denselben Gang zweimal entlanggegangen ist, merkt er, dass es derselbe ist, und verbindet die beiden Stellen. Ohne das wäre die Karte eine lange Kette wie deine Wegpunktliste, und Spot ginge jeden Umweg wieder. Für eine alte Karte gibt es den Knopf «Karte verbessern» (im Code `spot.process_map()`).

**3. Hinfahren.** Im eigenen Programm:

```python
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    spot.load_map("Schulhaus")        # die gespeicherte Karte laden
    print(spot.waypoints())           # die benannten Wegpunkte
    spot.localize()                   # wo bin ich? braucht einen AprilTag in Sicht
    if spot.navigate_to("Bibliothek"):
        print("angekommen")
```

`navigate_to` fährt Spot selbst dorthin, auf den Wegen der Karte, mit dem Tempodeckel aus spotlabs Einstellungen. Die Antwort ist `True`, wenn er angekommen ist. Mit `abbruch=` kannst du eine eigene Funktion mitgeben, die unterwegs immer wieder gefragt wird. Sagt sie `True`, hält Spot an.

```quiz punkte=2
? Warum braucht `spot.localize()` einen AprilTag in Sicht?
A) Weil Spot ohne Tag nicht weiss, welche Karte geladen ist.
B)* Nach dem Einschalten weiss Spot nicht, wo auf der Karte er steht. Ein Tag ist ein Ort, den er von der Aufnahme kennt. Sieht er ihn wieder, kann er seine Lage auf der Karte ausrechnen.
C) Weil der Tag Strom für die Kameras liefert.
D) Das stimmt nicht, `localize()` braucht nur die Füsse.
! Spots eigene Positionsangabe beginnt bei jedem Start neu bei null, und die Karte ist in einem anderen Rahmen gespeichert. Der Tag ist der **gemeinsame Punkt** in beiden: Spot weiss aus der Aufnahme, wo der Tag auf der Karte hängt, und sieht jetzt, wo der Tag relativ zu ihm hängt. Daraus folgt, wo er selbst steht, dieselbe Rechnung wie in Kapitel 7, nur umgekehrt.
```

```quiz punkte=2
? Bei der Aufnahme ist Spot einmal um einen Häuserblock gegangen: von A über B, C und D und wieder zurück zu A. Der Schleifenschluss hat nicht geklappt. Was passiert, wenn Spot danach von D zu A navigieren soll?
A) Er geht den kurzen Weg direkt von D nach A.
B)* Er geht den langen Weg zurück über C und B, denn ohne Schleifenschluss weiss die Karte nicht, dass der Anfang und das Ende der Runde derselbe Ort sind.
C) Er bleibt stehen, weil A zweimal auf der Karte steht.
D) Er findet A gar nicht.
! Ohne Schleifenschluss ist die Aufnahme eine Kette: A, B, C, D, A' — und A' ist für die Karte ein anderer Ort als A, auch wenn es derselbe ist. Spot kennt nur die Kette, also geht er sie zurück. Genau so macht es dein Programm aus dem letzten Abschnitt. Der Schleifenschluss ist der Schritt, der aus einer Kette ein **Netz** macht, darum der Name GraphNav (ein Graph ist ein Netz aus Punkten und Verbindungen).
```
