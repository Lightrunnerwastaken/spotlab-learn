---
nummer: 12
titel: Einem Menschen folgen
---

# Wo ist der Mensch?

In diesem Kapitel geht Spot einem Menschen hinterher. Das klingt nach einer einzigen Aufgabe, es sind aber zwei:

1. **Finden:** Wo ist der Mensch gerade? Die Antwort ist immer dieselbe Art von Zahlenpaar: eine **Peilung** in Grad (links positiv, wie in Kapitel 7) und ein **Abstand** in Metern.
2. **Fahren:** Wie muss Spot gehen und drehen, damit er dem Menschen folgt, ohne ihm zu nahe zu kommen?

spotlab trennt diese beiden Teile genau so. Der Teil, der findet, heisst **Finder**, der Teil, der fährt, heisst **Regler**. Ein Regler ist ein Programm, das immer wieder misst und daraus neu entscheidet, wie stark Spot lenkt und wie schnell er geht. Der Vorteil der Trennung: Man kann den Finder austauschen, und der Regler bleibt gleich.

Im Übungsraum trägt der Mensch **Tag 9 auf dem Rücken**. Dein Finder ist darum `spot.tags(id=9)`, das kennst du aus Kapitel 7. Auf der Karte ist der Mensch der orange Kreis; der schwarze Strich hinter ihm ist der Tag.

```spot raum=mensch-steht
import math
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    z = spot.state
    m = spot.tags(id=9)[0]
    print(f"Peilung {m.bearing:.0f}°, Abstand {m.distance:.2f} m")
    # Wo im Raum steht er? (Rechnung aus Kapitel 7)
    r = math.radians(z.heading + m.bearing)
    print(f"Er steht bei x = {z.x + m.distance * math.cos(r):.1f}, y = {z.y + m.distance * math.sin(r):.1f}")
```

> Am echten Spot braucht niemand einen Tag auf dem Rücken: spotlabs Folgemodus erkennt den **Körper** des Menschen in den Kamerabildern (mehr dazu im letzten Abschnitt). Für den Regler ist das egal, denn beide Finder liefern Peilung und Abstand. Im Übungsraum ist der Mensch übrigens kein Hindernis, Spot könnte durch ihn hindurchgehen. Die Prüfungen in diesem Kapitel messen deshalb den Abstand.

```quiz punkte=2
? Der Finder meldet: Peilung −60°, Abstand 2.0 m. Wo steht der Mensch, von Spot aus gesehen?
A) Links vorne, 2 m entfernt.
B)* Rechts vorne, 2 m entfernt, schon fast neben Spot.
C) Hinter Spot.
D) 60 cm rechts von Spot.
! Die Peilung ist ein Winkel: 0° ist geradeaus, positiv ist links, negativ rechts. −60° ist also deutlich rechts, aber noch vor Spot (hinten wäre über 90°). Der Abstand von 2.0 m ist die gerade Linie zum Menschen.
```

# Hinschauen

Der erste Teil des Reglers dreht Spot so, dass er den Menschen **anschaut**. Die Regel ist einfach: Je weiter der Mensch zur Seite steht, desto schneller dreht Spot. Ist die Peilung null, dreht er gar nicht.

| Drehtempo = K × Peilung

`K` ist eine Zahl, die du wählst. Mit `K = 1.2` dreht Spot bei 10° Peilung mit 12° pro Sekunde.

Damit Spot laufend neu lenken kann, benutzt du `spot.walk` mit `stop=False` (Kapitel 3): Der Befehl kehrt sofort zurück, und Spot fährt damit weiter, bis der nächste Befehl kommt. Nach `time.sleep(0.2)` misst das Programm neu und schickt den nächsten Befehl, fünfmal pro Sekunde. Und wenn das Programm hängen bleibt? Dann hört Spot nach **einer Sekunde** (`duration=1.0`) von selbst auf. Ein Befehl, der von selbst abläuft, heisst **Totmannschalter**: Bleiben die Befehle aus, steht Spot still.

In diesem Raum geht der Mensch vor Spot hin und her. Spot bleibt stehen und dreht sich nur mit:

```spot raum=mensch-quer
import math, time
from spotlab import connect

K = 1.2

with connect() as spot:
    spot.power_on()
    spot.stand()
    for takt in range(100):                 # 100 Takte à 0.2 s = 20 s
        tags = spot.tags(id=9)
        if tags:
            m = tags[0]
            spot.walk(wz=math.radians(K * m.bearing), duration=1.0, stop=False)
            if takt % 5 == 0:
                print(f"{takt * 0.2:4.1f} s   Peilung {m.bearing:6.1f}°")
        else:
            spot.stop()                     # niemand zu sehen: stehen bleiben
        time.sleep(0.2)
```

Die Peilung bleibt fast die ganze Zeit unter 10°: Spot schaut den Menschen an, während er geht. Probiere jetzt andere Werte für `K` aus, zum Beispiel 0.3 und 10, und beobachte die Peilung.

```quiz punkte=2
? Mit `K = 0.3` steht die Peilung am Ende bei −18°, obwohl der Mensch längst stillsteht. Warum dreht Spot nicht weiter?
A) Weil der Tag bei −18° nicht mehr zu sehen ist.
B)* Weil 0.3 × 18 nur gut 5° pro Sekunde ergibt. So langsames Drehen führt Spot gar nicht aus, er bleibt einfach stehen.
C) Weil `K` negativ sein müsste.
D) Weil `walk` mit `stop=False` nur einmal dreht.
! spotlabs Simulator macht hier dasselbe wie der echte Spot, gemessen in über 1700 Takten: Ein Drehtempo unter 0.125 rad/s (etwa 7° pro Sekunde) setzt Spot nicht um. Ein kleines `K` ist deshalb nicht nur langsam, es lässt einen Rest übrig, den Spot nie wegdreht. spotlabs eigener Regler hat aus demselben Grund ein **Totband**: Unter 4° Peilung dreht er absichtlich gar nicht, statt um null herum zu zappeln.
```

```quiz punkte=2
? Mit `K = 10` springt die Peilung im Takt zwischen etwa +10° und −9° hin und her. Was passiert da?
A) Der Finder misst ungenau.
B) Spot dreht zu langsam.
C)* Spot dreht in jedem Takt zu weit: Bis die nächste Messung kommt, ist er schon über den Menschen hinaus und muss zurückdrehen. Er pendelt.
D) Der Mensch geht im Zickzack.
! Zwischen zwei Messungen vergehen 0.2 s, und Spot braucht noch etwas Zeit, bis er einen neuen Befehl umsetzt. Wer in dieser Zeit mehr dreht, als die Peilung gross war, liegt danach auf der anderen Seite. Genau das ist am echten Spot passiert, als der Folgemodus nur zweimal pro Sekunde ein Bild bekam. Seitdem dreht spotlab in jedem Takt **höchstens die halbe Peilung**. Ein gutes `K` liegt dazwischen: schnell genug, um mitzukommen, langsam genug, um nicht zu pendeln.
```

# Abstand halten

Der zweite Teil des Reglers sorgt dafür, dass Spot hinterhergeht, aber nicht zu nahe kommt. spotlabs Folgemodus will **1.6 m** Abstand halten. Ist der Mensch weiter weg, geht Spot vorwärts, umso schneller, je grösser der Unterschied:

| Tempo = 0.6 × (Abstand − 1.6)

Dazu kommen drei Regeln, die spotlab genau so hat:

- **Nie rückwärts.** Kommt der Mensch näher, bleibt Spot stehen. Beim Folgen schaut Spot nach vorn, und hinter ihm prüft niemand, ob dort Platz ist.
- **Erst drehen, dann gehen.** Steht der Mensch mehr als 40° zur Seite, dreht Spot nur und geht nicht.
- **Ein Tempodeckel.** Höchstens 0.5 m/s, egal wie weit der Mensch weg ist.

Hier geht der Mensch weg, bleibt stehen, biegt ab und kommt am Ende auf Spot zu:

```spot raum=mensch-geht
import math, time
from spotlab import connect

WUNSCH = 1.6

with connect() as spot:
    spot.power_on()
    spot.stand()
    for takt in range(150):
        tags = spot.tags(id=9)
        if not tags:
            spot.stop()
            time.sleep(0.2)
            continue
        m = tags[0]
        drehen = max(-45, min(45, 1.2 * m.bearing))          # Grad pro Sekunde
        tempo = 0.0
        if abs(m.bearing) < 40 and m.distance > WUNSCH:
            tempo = min(0.5, 0.6 * (m.distance - WUNSCH))
        spot.walk(vx=tempo, wz=math.radians(drehen), duration=1.0, stop=False)
        if takt % 10 == 0:
            print(f"{takt * 0.2:4.1f} s   Abstand {m.distance:4.2f} m   Tempo {tempo:4.2f} m/s")
        time.sleep(0.2)
```

Am Ende kommt der Mensch bis auf 0.8 m heran, und Spot bleibt stehen. Er weicht nicht zurück, denn das ist die Regel «nie rückwärts».

```quiz punkte=2
? Jemand löscht in der Zeile `if abs(m.bearing) < 40 and m.distance > WUNSCH:` den Teil `and m.distance > WUNSCH`. Was tut Spot, wenn der Mensch 1.0 m vor ihm steht?
A) Er bleibt stehen wie vorher.
B) Er geht langsam weiter vorwärts.
C)* Er geht rückwärts, denn 0.6 × (1.0 − 1.6) ergibt −0.36 m/s.
D) Das Programm stürzt ab, weil das Tempo negativ ist.
! Die Formel gibt bei zu kleinem Abstand ein negatives Tempo, und ein negatives `vx` heisst rückwärts. Die Bedingung `m.distance > WUNSCH` ist also keine Kleinigkeit, sie ist die Regel «nie rückwärts». In spotlabs Regler steht sie als eigene Zeile, und die Formel wird mit `max(0.0, …)` zusätzlich nach unten begrenzt. Eine Sicherheitsregel bekommt lieber zwei Schranken als eine.
```

# Hinter der Tür

Jetzt geht der Mensch durch die Wohnung aus Kapitel 8: aus dem linken Zimmer durch die Tür nach rechts oben und dann durch die zweite Tür ins Zimmer unten rechts. Probiere den Regler von eben hier aus:

```spot raum=mensch-wohnung
import math, time
from spotlab import connect

WUNSCH = 1.6
zuletzt = 0

with connect() as spot:
    spot.power_on()
    spot.stand()
    for takt in range(200):
        tags = spot.tags(id=9)
        if not tags:
            spot.stop()
            time.sleep(0.2)
            continue
        zuletzt = takt
        m = tags[0]
        drehen = max(-45, min(45, 1.2 * m.bearing))
        tempo = 0.0
        if abs(m.bearing) < 40 and m.distance > WUNSCH:
            tempo = min(0.5, 0.6 * (m.distance - WUNSCH))
        spot.walk(vx=tempo, wz=math.radians(drehen), duration=1.0, stop=False)
        time.sleep(0.2)
    print(f"Mensch nicht mehr zu sehen seit {(200 - zuletzt) * 0.2:.0f} s")
```

Spot folgt bis kurz vor die Tür, dann ist der Mensch weg. Der Türrahmen steht zwischen den beiden, und ohne Sichtlinie sieht Spot den Tag nicht mehr (Kapitel 7). Von da an bleibt Spot stehen und wartet.

Die naheliegende Verbesserung: Spot merkt sich, **wo er den Menschen zuletzt gesehen hat**, und geht dorthin. So einen Punkt nennt spotlab einen **Merkpunkt**. Im Übungsraum nachgeprüft: Geht Spot von seinem Platz aus geradewegs zum Merkpunkt, stösst er an den Türrahmen. Der Mensch ist um die Ecke gegangen, und die gerade Linie schneidet sie ab.

Die Lösung kennst du aus Kapitel 11: **Wegpunkte**. Spot merkt sich nicht nur den letzten Ort, sondern alle Orte, an denen er den Menschen gesehen hat, der Reihe nach. Das ist die **Spur** des Menschen, und dort ist der Mensch gegangen, also ist dort Platz. Spot geht die Spur ab, Punkt für Punkt, wie ein Hund, der einer Fährte folgt.

```quiz punkte=2
? Spot folgt der Spur des Menschen und lenkt immer auf den **ältesten** Punkt, den er noch nicht erreicht hat. Warum nicht einfach auf den neuesten?
A) Der neueste Punkt ist ungenauer.
B)* Der neueste Punkt ist der Ort, an dem der Mensch gerade ist. Darauf zuzulenken ist dasselbe wie vorher: Die gerade Linie schneidet die Ecke ab. Nur die alten Punkte führen um die Ecke herum.
C) Weil die Liste sonst zu lang wird.
D) Das ist egal, beide führen zum Ziel.
! Die Spur ist nur dann nützlich, wenn Spot sie **der Reihe nach** abgeht. Erreichte Punkte streicht er vorne aus der Liste. So zeigt der erste Punkt der Liste immer dorthin, wo der Mensch als Nächstes gegangen ist. Den **Abstand** misst Spot trotzdem zum neuesten Punkt, denn dort ist der Mensch.
```

Baue jetzt einen Regler, der der Spur folgt. Der Mensch geht durch beide Türen, und Spot muss mitkommen, ohne anzustossen und ohne dem Menschen näher als 1 m zu kommen. Dein Programm läuft von drei Startplätzen aus.

```aufgabe raum=mensch-wohnung punkte=8 starts=2,0.8,90;2.6,1.1,180;1.8,1,0
ziel: mensch_abstand 1.0
ziel: mensch_nah 2.5
ziel: nicht_angestossen
tipp: Den Ort des Menschen rechnest du wie im ersten Abschnitt aus: `ort_von(z, m)`. Hänge ihn nur an die Spur an, wenn er mehr als 0.2 m vom letzten Punkt entfernt ist, sonst wächst die Liste mit lauter gleichen Punkten.
tipp: Erreichte Punkte streichen: `while len(spur) > 1 and math.hypot(spur[0][0] - z.x, spur[0][1] - z.y) < 0.3: spur.pop(0)`. Den letzten Punkt lässt du stehen, er ist der Mensch.
tipp: Peilung zum Spurpunkt: `(math.degrees(math.atan2(dy, dx)) - z.heading + 180) % 360 - 180` mit `dx, dy = ziel[0] - z.x, ziel[1] - z.y`. Den Abstand misst du zum neuesten Punkt `spur[-1]`.
tipp: Siehst du den Menschen gerade nicht, ist der neueste Spurpunkt nur der Ort, an dem er verschwunden ist, nicht er selbst. Dann geh die Spur ganz bis ans Ende (Wunschabstand 0 statt 1.6), sonst bleibt Spot 1.6 m davor stehen und sieht ihn nie wieder.
---
import math, time
from spotlab import connect

WUNSCH = 1.6
spur = []          # Orte, an denen der Mensch war, der Reihe nach

def ort_von(z, m):
    r = math.radians(z.heading + m.bearing)
    return (z.x + m.distance * math.cos(r), z.y + m.distance * math.sin(r))

with connect() as spot:
    spot.power_on()
    spot.stand()
    for takt in range(200):
        z = spot.state
        tags = spot.tags(id=9)
        # 1. Ort des Menschen an die Spur hängen

        # 2. erreichte Punkte vorne streichen

        if not tags:
            spot.stop()
            time.sleep(0.2)
            continue
        # 3. statt auf den Menschen auf den ersten Punkt der Spur lenken
        m = tags[0]
        drehen = max(-45, min(45, 1.2 * m.bearing))
        tempo = 0.0
        if abs(m.bearing) < 40 and m.distance > WUNSCH:
            tempo = min(0.5, 0.6 * (m.distance - WUNSCH))
        spot.walk(vx=tempo, wz=math.radians(drehen), duration=1.0, stop=False)
        time.sleep(0.2)
    spot.stop()
```

Schau dir die Wege auf der Karte an: Spot geht durch die Türen dort, wo auch der Mensch ging, nicht quer über die Ecke.

# Am echten Spot

Am echten Spot musst du den Folgemodus nicht selbst bauen. spotlab hat ihn eingebaut, im Modul `spotlab.workshop.folgen`. Den Regler daraus kannst du hier direkt ausprobieren. Die Funktion `befehl` bekommt Peilung und Abstand und antwortet mit Tempo (m/s) und Drehtempo (rad/s):

```spot raum=keiner
from spotlab.workshop import folgen

for peilung, abstand in [(20, 2.5), (60, 2.5), (0, 1.2), (2, 3.0)]:
    tempo, drehen = folgen.befehl(folgen.Ziel(peilung, abstand))
    print(f"Peilung {peilung:3}°, Abstand {abstand} m  ->  Tempo {tempo:.2f} m/s, Drehen {drehen:.2f} rad/s")
```

Vergleiche mit deinem Regler: Bei 60° dreht er nur (erst drehen, dann gehen), bei 1.2 m steht er (nie rückwärts), bei 2° Peilung dreht er nicht (Totband). Und bei 3 m geht er mit 0.75 m/s schneller als dein Deckel: Weit weg darf spotlabs Regler bis 1 m/s gehen, damit Spot einen schnellen Menschen nicht verliert. Dafür prüft er dann weiter voraus, ob Platz ist.

Der ganze Folgemodus heisst `folgen.folge`. Er läuft auch im Übungsraum, hier mit einem Tag als Finder, 15 Sekunden lang:

```spot raum=mensch-wohnung
import time
from spotlab import connect
from spotlab.workshop import folgen

with connect() as spot:
    spot.power_on()
    spot.stand()
    ende = time.monotonic() + 15
    folgen.folge(spot, folgen.tag_finder(9), blick_grad=0,
                 laeuft=lambda: time.monotonic() < ende)
```

Er bleibt vor der Tür stehen und sagt warum, zum Beispiel «nur 0.6 m frei voraus». spotlabs Folgemodus hat **Schranken**, die vor jedem Schritt prüfen, ob es sicher ist. Eine davon schaut im Hindernisgitter (Kapitel 6), ob vor Spot genug Platz ist. Eine Spur wie in deinem Programm hat er nicht: Er ist auf **Sicherheit** gebaut, nicht darauf, möglichst weit zu kommen. Verliert er den Menschen, dreht er sich höchstens noch zu der Stelle, an der er ihn zuletzt sah, und dann wartet er.

So startest du ihn am echten Spot. Das Programm liegt auch in spotlab im Projekt «Beispiele» als `folgen.py`:

```python
import spotlab
from spotlab.workshop import folgen

with spotlab.connect() as spot:
    spot.power_on()
    spot.stand()
    finder = folgen.koerper_finder()                 # erkennt den Körper in den Kamerabildern
    folgen.folge(spot, finder,
                 gesten=folgen.gesten_leser(finder), # Handzeichen verstehen
                 lauf_dir=spot.recorder.dir)
    spot.sit()
```

Was dabei passiert:

- **Finder:** `koerper_finder()` sucht in den Bildern der Frontkameras nach einem Menschen und misst mit den Tiefenkameras, wie weit er weg ist. Er sucht den Körper, nicht das Gesicht: Auf 1.5 m Abstand reicht das Bild nur bis etwa 1.2 m Höhe, weil die Kameras nach unten schauen. Von einem stehenden Menschen ist dann der Kopf gar nicht im Bild.
- **Licht:** Die LEDs am Kopf zeigen, was Spot gerade denkt: **gelb** heisst «ich suche», **blau** heisst «ich folge dir», **rot** heisst «per Handzeichen angehalten».
- **Handzeichen:** Die offene Hand (Finger nach oben, Handfläche zu Spot) heisst **Halt**, der Daumen hoch heisst **Weiter**. Halte das Zeichen vor der Brust, ein bis zwei Meter vor Spot, etwa zwei Sekunden lang.
- **Schranken:** nie näher als 1 m, nie rückwärts, ohne Ziel sofort stehen, vorwärts nur, wenn vorne frei ist und nichts über dem Weg hängt (zum Beispiel eine Tischplatte).

> Spot bewegt sich dabei **von selbst**. Folgen nur auf einer freien Fläche, mit Aufsicht und mit dem Tablet samt Not-Aus in der Hand.

```quiz punkte=2
? Eine Schranke im Folgemodus prüft mit den Tiefenkameras, ob über dem Weg etwas hängt. Einmal kommt das Tiefenbild kaputt an und lässt sich nicht lesen. Was sollte die Schranke tun?
A) Die Fahrt erlauben, denn sie hat ja nichts gesehen.
B)* Die Fahrt verbieten, bis wieder ein lesbares Bild da ist.
C) Den alten Wert von vor einer Minute nehmen.
D) Das Programm mit einem Fehler beenden.
! «Nichts gesehen» ist nicht «frei» (Kapitel 10). Eine Schranke, die bei einer Störung durchwinkt, schützt genau dann nicht, wenn etwas schiefgeht. In spotlab gilt darum für jede Schranke im Folgemodus: Kann sie ihre Daten nicht lesen, verbietet sie die Fahrt. Das nennt man **fail-closed**, im Zweifel zu. Spot bleibt dann kurz stehen. Das ist lästig, aber ungefährlich.
```

```quiz punkte=2
? Du folgst mit Spot durch den Gang. Plötzlich leuchten seine LEDs gelb, und er bleibt stehen. Was ist der beste nächste Schritt?
A) Das Programm neu starten.
B) Mit der offenen Hand Halt zeigen.
C)* Spot hat dich verloren und sucht. Stell dich gut sichtbar vor ihn, ein bis zwei Meter entfernt, damit sein Finder dich wieder findet.
D) Mit dem Daumen hoch Weiter zeigen.
! Gelb heisst «kein Ziel, er sucht». Ein Handzeichen hilft da nicht: Zeichen versteht Spot nur bei dem Menschen, dem er gerade folgt, und gerade folgt er niemandem. Das Licht ist genau dafür da: Du siehst Spot an, was er denkt, ohne auf den Laptop zu schauen.
```
