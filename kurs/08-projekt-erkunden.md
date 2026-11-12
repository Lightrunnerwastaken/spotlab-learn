---
nummer: 8
titel: Projekt: Unbekannter Raum
---

# Erkunden ohne Karte

Stell dir vor, Spot steht in einem Gebäude, das er nie gesehen hat. Er hat keinen Plan. Er weiss nur, was er **jetzt gerade** sieht: wo es frei ist (`look`) und ob ein Tag in der Nähe hängt (`tags`). Daraus soll er sich selbst einen Weg suchen.

In diesem Kapitel übst du das in einer **Wohnung** mit drei Zimmern und zwei Türen. Du siehst den Grundriss rechts auf der Karte. **Dein Programm sieht ihn nicht.** Es muss so tun, als wäre alles unbekannt.

Die einfachste Idee ist eine feste Regel, ein **Reflex**: Ist vorne frei, geh geradeaus. Sonst dreh dich nach links, sonst nach rechts, sonst um.

```spot raum=wohnung start=4,1.2,0
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    for schritt in range(12):
        blick = spot.look(max_distance=1.0, start=0.6, margin=0.35)
        if blick.front.status == "clear":
            print(schritt, "geradeaus")
            spot.move(forward=0.5)
        elif blick.left.status == "clear":
            print(schritt, "links")
            spot.move(turn=90)
        elif blick.right.status == "clear":
            print(schritt, "rechts")
            spot.move(turn=-90)
        else:
            print(schritt, "umdrehen")
            spot.move(turn=180)
```

Spot kommt keinen Zentimeter vom Fleck. Vorne steht die Kiste, links und rechts sind die Wände näher als 1 m plus Sicherheitsabstand. Also dreht er sich um. Jetzt steht er in derselben Lage, nur gespiegelt: vorne die Wand, links und rechts zu eng. Also dreht er sich wieder um. Und so weiter.

Das ist kein Zufall, sondern liegt an der Art der Regel: **Eine Regel ohne Gedächtnis gibt in derselben Lage immer dieselbe Antwort.** Kommt Spot wieder in eine Lage, in der er schon war, macht er wieder dasselbe. Von anderen Startplätzen aus kommt dieselbe Regel weiter herum. Aber darauf kannst du dich nicht verlassen.

```quiz punkte=2
? Eine Mitschülerin schlägt vor: «Wenn vorne zu ist, dreh dich in eine **zufällige** freie Richtung.» Was stimmt?
A) Damit findet Spot sicher jeden Ort in der Wohnung, und zwar schnell.
B) Das ändert nichts: Spot bleibt genauso stecken wie vorher.
C)* Spot kommt aus der Falle heraus, läuft aber oft durch Stellen, an denen er schon war. Und jeder Lauf ist anders, darum ist schwer zu prüfen, ob das Programm funktioniert.
D) Zufall geht in Python nicht, ohne dass man ein Paket installiert.
! Zufall bricht die Wiederholung, denn dieselbe Lage führt nicht mehr immer zur selben Antwort. Aber Spot weiss immer noch nicht, wo er schon war: Er läuft blind hin und her, und ob er die zweite Tür je findet, ist Glückssache. Dazu kommt ein praktisches Problem: Wenn jeder Lauf anders ist, kann ein Fehler einmal auftreten und beim nächsten Mal nicht. Besser ist es, Spot ein **Gedächtnis** zu geben. (`import random` gehört übrigens zu Python, D ist falsch.)
```

# Wo war ich schon?

Ein Mensch, der ein fremdes Haus erkundet, merkt sich, wo er schon war, und geht lieber dorthin, wo er noch nicht war. Das bringen wir Spot jetzt bei.

## Den Boden in Felder teilen

Wir legen gedanklich ein Gitter aus Feldern von 50 × 50 cm über den Boden, wie ein Schachbrett. Zu welchem Feld ein Punkt gehört, rechnet diese Funktion aus:

```python
def feld(x, y):
    return (int(x // 0.5), int(y // 0.5))
```

`//` teilt und rundet ab: `1.3 // 0.5` ist `2.0`, denn 0.5 passt zweimal ganz in 1.3. Der Punkt (1.3, 0.2) liegt also im Feld `(2, 0)`. Ein Feld ist ein Paar aus zwei Zahlen, in Python ein **Tupel**.

## Mitzählen mit einem Dictionary

Für jedes Feld wollen wir zählen, wie oft Spot dort war. Dafür gibt es in Python das **Dictionary** (Wörterbuch). Eine Liste ist durchnummeriert. Ein Dictionary dagegen ordnet einem **Schlüssel** einen **Wert** zu: hier jedem Feld seine Besuchszahl.

```python
besuche = {}                                     # leer
besuche[(2, 0)] = besuche.get((2, 0), 0) + 1     # Feld (2, 0) einmal besucht
besuche[(2, 0)] = besuche.get((2, 0), 0) + 1     # und noch einmal
print(besuche)                                   # {(2, 0): 2}
print(besuche.get((5, 5), 0))                    # 0: dort war Spot nie
```

`besuche.get(feld, 0)` gibt die Zahl für dieses Feld zurück, oder 0, wenn das Feld noch gar nicht im Dictionary steht.

## Die Regel mit Gedächtnis

Jetzt die neue Regel. Bei jedem Schritt:

1. Zähle das Feld, auf dem Spot steht, als besucht.
2. Schau rundum, alle 15°.
3. Unter den **freien** Richtungen nimm die, bei der das Feld **1 m voraus** am **seltensten** besucht ist.
4. Dreh dich dorthin und geh 0.5 m.

Spot startet am selben Ort, an dem der Reflex steckengeblieben ist. Am Ende zeichnet das Programm aus dem Dictionary eine Karte: `.` heisst nie dort gewesen, eine Zahl sagt, wie oft.

```spot raum=wohnung start=4,1.2,0
import math
from spotlab import connect

def feld(x, y):
    return (int(x // 0.5), int(y // 0.5))

besuche = {}

with connect() as spot:
    spot.power_on()
    spot.stand()
    for schritt in range(30):
        z = spot.state
        hier = feld(z.x, z.y)
        besuche[hier] = besuche.get(hier, 0) + 1

        blick = spot.look(max_distance=1.0, start=0.6, margin=0.35)
        bester_winkel = None
        beste_zahl = None
        for winkel in sorted(range(-180, 180, 15), key=abs):
            if blick.direction(winkel).status != "clear":
                continue
            r = math.radians(z.heading + winkel)
            dort = feld(z.x + 1.0 * math.cos(r), z.y + 1.0 * math.sin(r))
            zahl = besuche.get(dort, 0)
            if beste_zahl is None or zahl < beste_zahl:
                bester_winkel = winkel
                beste_zahl = zahl

        if bester_winkel is None:
            spot.move(turn=90)
        else:
            spot.move(turn=bester_winkel)
            spot.move(forward=0.5)

    # Die eigene Karte: oben ist y = 5 m, links ist x = 0
    for reihe in range(9, -1, -1):
        zeile = ""
        for spalte in range(16):
            n = besuche.get((spalte, reihe), 0)
            zeile += "." if n == 0 else str(min(n, 9))
        print(zeile)
```

Diesmal kommt Spot vom Platz neben der Kiste los, durch die Tür ins obere Zimmer und von dort weiter ins linke. Die Zahlenkarte in der Ausgabe ist **Spots eigene Karte**: Sie zeigt nicht, wie die Wohnung aussieht, sondern wo er gewesen ist. Vergleiche sie mit dem Grundriss.

Zwei Kleinigkeiten im Code:

- `sorted(range(-180, 180, 15), key=abs)` ordnet die Winkel nach ihrer Grösse ohne Vorzeichen: 0, 15, −15, 30, −30, … Bei Gleichstand gewinnt damit die Richtung, die am wenigsten Drehung braucht. Spot geht lieber geradeaus weiter als im Zickzack.
- `continue` springt sofort zum nächsten Winkel. Verdeckte Richtungen werden so gar nicht erst bewertet.

```quiz punkte=2
? Ein Schüler merkt sich die Felder in einer Menge (`besucht = set()`), also nur **ob** Spot dort war, nicht **wie oft**. Die Regel heisst dann: «Nimm eine freie Richtung, deren Feld noch nicht besucht ist.» Wann gibt das Probleme?
A) Nie, «wie oft» ist eine überflüssige Information.
B) Sofort, weil man Tupel nicht in eine Menge legen kann.
C)* Wenn rundherum alle Felder schon besucht sind. Dann sind alle Richtungen gleich gut, Spot nimmt immer die erste (geradeaus) und kann wieder hin und her pendeln.
D) Wenn Spot genau auf der Grenze zwischen zwei Feldern steht.
! Am Anfang ist alles unbesucht, da reicht ja/nein. Aber spätestens in einem Zimmer, das Spot schon kennt, sind alle Nachbarfelder «besucht», und die Regel kann nicht mehr unterscheiden. Mit Zählern schon: Ein Feld, auf dem er zweimal war, ist besser als eines mit fünf Besuchen. So drängt ihn die Regel langsam aus bekannten Gegenden hinaus, auch durch Gebiete, die er schon kennt.
```

# Ein Objekt im Unbekannten finden

Jetzt verbinden wir das Erkunden mit Kapitel 7: Spot erkundet, bis er **Tag 5** sieht, und hört dann auf. Dazu kommt am Anfang jedes Schritts eine Frage dazu:

```python
        if spot.tags(id=5):
            print("Tag 5 gefunden nach", schritt, "Schritten.")
            break
```

`break` beendet die `for`-Schleife sofort. Die Zahl in `range(...)` ist damit nur noch die **Notbremse**: So viele Schritte darf Spot höchstens machen, wenn er den Tag nie findet.

```spot raum=wohnung start=1,1,90
import math
from spotlab import connect

def feld(x, y):
    return (int(x // 0.5), int(y // 0.5))

besuche = {}

with connect() as spot:
    spot.power_on()
    spot.stand()
    for schritt in range(80):
        if spot.tags(id=5):
            print("Tag 5 gefunden nach", schritt, "Schritten.")
            break
        z = spot.state
        hier = feld(z.x, z.y)
        besuche[hier] = besuche.get(hier, 0) + 1

        blick = spot.look(max_distance=1.0, start=0.6, margin=0.35)
        bester_winkel = None
        beste_zahl = None
        for winkel in sorted(range(-180, 180, 15), key=abs):
            if blick.direction(winkel).status != "clear":
                continue
            r = math.radians(z.heading + winkel)
            dort = feld(z.x + 1.0 * math.cos(r), z.y + 1.0 * math.sin(r))
            zahl = besuche.get(dort, 0)
            if beste_zahl is None or zahl < beste_zahl:
                bester_winkel = winkel
                beste_zahl = zahl

        if bester_winkel is None:
            spot.move(turn=90)
        else:
            spot.move(turn=bester_winkel)
            spot.move(forward=0.5)
    else:
        print("Nach 80 Schritten kein Tag 5.")
```

Spot startet im linken Zimmer, findet die Tür ins obere Zimmer und hält dort an: Durch die zweite Tür hindurch sieht er Tag 5. Hineingehen muss er dafür nicht. Es reicht, dass die Sicht frei ist (Kapitel 7). Das Rechnen dauert hier etwas länger als bisher: Spot macht jetzt viele Dutzend Schritte, und jeder `look` muss das ganze Hindernisgitter berechnen.

Neu ist das `else` nach der `for`-Schleife. Es läuft nur, wenn die Schleife **ohne** `break` zu Ende ging, hier also, wenn Spot den Tag nie gesehen hat.

```quiz punkte=2
? Was passiert, wenn du `if spot.tags(id=5): ... break` ans **Ende** des Schleifenkörpers verschiebst, also nach dem `spot.move(forward=0.5)`?
A) Das Programm stürzt ab, weil `break` am Ende einer Schleife nicht erlaubt ist.
B) Spot findet den Tag nie mehr.
C)* Fast nichts: Spot hört nach dem Schritt auf, in dem er den Tag zum ersten Mal sieht. Nur ein Tag, der schon vom **Startplatz** aus sichtbar ist, kostet jetzt einen unnötigen Schritt.
D) Spot macht immer genau 80 Schritte.
! Die Frage wird in jedem Durchgang gestellt, nur an einer anderen Stelle. Vorher fragte Spot, **bevor** er sich bewegt, und blieb stehen, wenn der Tag schon zu sehen war. Danach macht er zuerst einen Schritt. Meistens ist das egal. Aber stell dir vor, der Tag hängt direkt neben dem Startplatz und vorne ist eine Treppe: Dann ist «erst schauen, dann gehen» die sicherere Reihenfolge.
```

# Dein eigenes Erkundungsprogramm

Jetzt baust du das Erkundungsprogramm selbst zusammen. Spot startet an **drei verschiedenen Orten** in der Wohnung. Von keinem aus sieht er Tag 5 sofort.

Dein Programm soll:

- die Wohnung erkunden, bis Tag 5 in Sicht ist,
- dann ausrechnen, **wo im Raum** Tag 5 hängt (wie in Kapitel 7),
- das ausgeben, genau in dieser Form: `Tag 5 hängt bei x = 7.9, y = 0.8`,
- und dabei nirgends anstossen.

Die Zahlen kennst du schon von der Karte, und du könntest sie einfach hinschreiben. Am echten Spot in einem fremden Gebäude kennst du sie aber vorher nicht. Darum: Dein Programm soll sie **selbst** herausfinden, aus dem, was Spot sieht.

```aufgabe raum=wohnung punkte=8 starts=1,1,90;7,4,180;1,4.5,-90
ziel: ausgabe Tag 5 hängt bei x = 7.9, y = 0.8
ziel: nicht_angestossen
ziel: aufgerufen tags
tipp: Die Erkundung aus «Ein Objekt im Unbekannten finden» funktioniert schon. Du brauchst dazu nur noch die Rechnung aus Kapitel 7: `richtung = math.radians(z.heading + tag.bearing)`, dann `tag_x = z.x + tag.distance * math.cos(richtung)`, und dasselbe mit `sin` für `tag_y`.
tipp: Die Ausgabe muss genau stimmen. Mit `print(f"Tag 5 hängt bei x = {tag_x:.1f}, y = {tag_y:.1f}")` steht da eine Stelle nach dem Komma.
tipp: Hört Spot auf, ohne den Tag zu finden? Dann ist die Notbremse zu knapp. Von den drei Startplätzen aus braucht die Regel aus diesem Kapitel zwischen 30 und 45 Schritte.
---
import math
from spotlab import connect

def feld(x, y):
    return (int(x // 0.5), int(y // 0.5))

besuche = {}

with connect() as spot:
    spot.power_on()
    spot.stand()
    for schritt in range(80):
        # 1. Sieht Spot Tag 5? Dann ausrechnen, wo er hängt, ausgeben und aufhören.

        # 2. Das aktuelle Feld als besucht zählen.

        # 3. Rundum schauen und die beste freie Richtung wählen.

        # 4. Dorthin drehen und 0.5 m gehen.

        pass
```

## Ideen für eigene Projekte

Wenn deine Lösung läuft, hast du einen kleinen Erkundungsroboter. Hier sind Ideen, wie du ihn ausbauen kannst. Dafür gibt es keine Punkte, nur Spot.

- **Hingehen:** Wenn Spot den Tag gefunden hat, geht er hin und hält 0.8 m davor an, wie in Kapitel 7. Aber Vorsicht: Spot sieht den Tag oft durch eine Tür hindurch, und der gerade Weg dorthin kann eine Wand streifen. Wie findest du einen sicheren Weg?
- **Eine bessere Karte:** Bisher merkt sich Spot nur, wo **er** war. Mit `spot.obstacles()` (Kapitel 6) kann er sich auch merken, wo er **Hindernisse** gesehen hat, und eine Karte mit `#` für Wände zeichnen.
- **Schneller erkunden:** Wie viele Schritte braucht deine Regel? Probier andere Werte aus: Felder von 1 m statt 0.5 m, Schritte von 0.8 m, Strahlen alle 10°. Was wird besser, was schlechter? Vorsicht: Mehr Tempo heisst oft mehr Anstossen.
- **Heimweg:** Spot merkt sich bei jedem Schritt seine Position in einer Liste. Wenn er den Tag gefunden hat, geht er den Weg rückwärts wieder zum Start.
