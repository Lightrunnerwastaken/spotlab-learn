---
nummer: 6
titel: Hindernissen ausweichen
---

# Links oder rechts? Entscheiden mit if

In Kapitel 5 ist Spot stehen geblieben, sobald etwas im Weg war. Jetzt soll er **ausweichen**. Dafür muss dein Programm entscheiden: links herum oder rechts herum?

Der Raum «Durchgang» hat zwei Zimmer, die durch eine Tür verbunden sind. Spot steht vor einer Kiste.

```spot raum=durchgang start=1,3.2,0
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()

    blick = spot.look(start=0.6)
    print("vorne:", blick.front.status, " links:", blick.left.status, " rechts:", blick.right.status)

    if blick.front.status == "clear":
        print("Frei, ich gehe geradeaus.")
        spot.move(forward=0.5)
    elif blick.left.status == "clear":
        print("Vorne zu, ich weiche nach links aus.")
        spot.move(left=0.8)
    elif blick.right.status == "clear":
        print("Vorne zu, ich weiche nach rechts aus.")
        spot.move(left=-0.8)
    else:
        print("Überall zu. Ich bleibe stehen.")
```

So liest Python das:

- `if` prüft die erste Bedingung. Ist sie wahr, laufen die eingerückten Zeilen darunter, und **alle anderen Teile werden übersprungen**.
- `elif` («else if») wird nur geprüft, wenn alles davor falsch war.
- `else` läuft, wenn keine der Bedingungen wahr war.

Darum weicht Spot hier nach rechts aus, obwohl rechts nur als dritte Möglichkeit drankommt: vorne ist die Kiste, links ist die Wand zu nahe.

```quiz punkte=2
? Spot steht vor einer Wand. Links und rechts ist frei. Was macht dieses Programm?
| if blick.left.status == "clear":
|     spot.move(left=0.8)
| if blick.right.status == "clear":
|     spot.move(left=-0.8)
A) Es weicht nach links aus.
B) Es weicht nach rechts aus.
C)* Es geht nach links und danach wieder nach rechts, steht also am Ende fast wieder am selben Ort.
D) Python meldet einen Fehler, weil ein else fehlt.
! Hier stehen zwei getrennte `if`, kein `elif`. Python prüft deshalb **beide**: Links ist frei, also geht Spot nach links. Danach ist rechts immer noch frei (die Messung `blick` ist ja von vorher), also geht er wieder zurück. Mit `elif` würde der zweite Teil übersprungen. Ein `else` braucht man übrigens nie zwingend.
```

# In alle Richtungen schauen

Vier Richtungen sind wenig. Mit `blick.direction(winkel)` fragst du jeden beliebigen Winkel ab. Der Winkel ist relativ zu Spots Blick, wie bei `move(turn=...)`: 0 ist vorne, positiv ist links, negativ ist rechts.

Mit einer Schleife tastet Spot einen ganzen Halbkreis ab. Das Programm zeichnet für jede Richtung einen Balken: je länger, desto mehr Platz.

```spot raum=durchgang start=3,2,90
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    blick = spot.look(max_distance=1.8, start=0.6)
    for winkel in range(-90, 91, 15):
        strahl = blick.direction(winkel)
        if strahl.status == "clear":
            balken = "#" * 18 + "  frei"
        elif strahl.status == "blocked":
            balken = "#" * int(strahl.distance * 10) + f"  {strahl.distance:.2f} m"
        else:
            balken = "?"
        print(f"{winkel:+4d}°  {balken}")
```

`range(-90, 91, 15)` zählt von −90 bis 90 in Schritten von 15. Die 91 ist Absicht: `range` hört **vor** der zweiten Zahl auf.

Spot schaut nach oben (90°). Rechts von ihm, bei −90°, ist der Balken lang: dort liegt die Tür ins andere Zimmer.

```quiz punkte=2
? Spot steht bei x = 3, y = 2 und schaut nach oben (heading 90°). Du willst wissen, ob es in Richtung **Osten** (grössere x-Werte, heading 0°) frei ist. Welchen Winkel gibst du `direction` mit?
A) `direction(0)`
B) `direction(90)`
C)* `direction(-90)`
D) `direction(180)`
! `direction` rechnet relativ zu Spots Blick. Osten liegt bei 0° im Raum, Spot schaut nach 90°. Der Unterschied ist 0 − 90 = **−90**: also rechts von Spot. Genau diese Rechnung (Ziel im Raum minus eigener Blick) brauchst du gleich in der Aufgabe.
```

# Was Spot sieht

Woher weiss `look`, was frei ist? Spot baut aus seinen Tiefenkameras ein **Hindernisgitter**: ein Raster aus kleinen Feldern von 3 cm, das um ihn herum liegt. Für jedes Feld weiss er, wie weit es bis zum nächsten Hindernis ist — oder dass er es nicht weiss.

Mit `spot.obstacles()` bekommst du dieses Gitter selbst. Das Programm hier malt es als Bild: `#` ist ein Hindernis, `.` ist frei, `?` ist unbekannt. Jedes Zeichen ist 25 cm.

```spot raum=durchgang start=1,2,0
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    gitter = spot.obstacles()
    for zeile in range(16, -1, -1):          # von oben (y = 4 m) nach unten
        y = zeile * 0.25
        bild = ""
        for spalte in range(0, 37):          # von links (x = 0) nach rechts (x = 9 m)
            x = spalte * 0.25
            abstand = gitter.distance_at(x, y)
            if abstand is None:
                bild += "?"
            elif abstand < 0.15:
                bild += "#"
            else:
                bild += "."
        print(bild)
```

Vergleiche das Bild mit der Karte daneben. Zwei Dinge fallen auf:

- **Spot sieht nur etwa 1.9 m weit.** Das Gitter ist ein Quadrat von knapp 4 m um ihn herum, am echten Spot genau gleich. Alles weiter weg ist `?`. Darum hat es keinen Sinn, `look` mit `max_distance=5` aufzurufen.
- **Direkt unter ihm ist ein `?`.** Das ist der blinde Fleck aus Kapitel 5.

> Am echten Spot liegt das Gitter in einem eigenen Koordinatensystem (es heisst «vision»), das mit der Zeit etwas von `spot.state` abweicht. Wer das Gitter selbst ausliest, nimmt Position und Blick deshalb aus `spot.look()` (`blick.position`, `blick.heading`) und nicht aus `spot.state`. Im Simulator ist beides gleich.

# Spot ist breiter als ein Strahl

`look` prüft einen **Strahl**: eine dünne Linie. Spot ist aber rund 50 cm breit. Damit er trotzdem nirgends anstösst, hält `look` einen **Sicherheitsabstand** zu Hindernissen ein: das ist der Parameter `margin`, normal 0.3 m. Liegt ein Hindernis näher als 0.3 m neben dem Strahl, gilt der Strahl als `blocked`.

Reicht das? Spot steht hier schräg neben der Ecke der Kiste. Der Strahl nach vorne ist frei — und trotzdem:

```spot raum=durchgang start=1.68,2.63,-15 fehler=ja
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    blick = spot.look(max_distance=1.2, start=0.6, margin=0.3)
    print("vorne:", blick.front.status)
    spot.move(forward=0.3)
    print("geschafft")
```

Spot stösst an die Ecke der Kiste (roter Kreis auf der Karte). Der Grund: `look` prüft erst ab `start=0.6`. Die Ecke liegt näher, schräg vor ihm, genau im Stück, das nicht geprüft wird. Spots halbe Breite (etwa 0.27 m) und der Sicherheitsabstand (0.3 m) liegen zu nahe beieinander.

Jetzt dasselbe mit einem grösseren Sicherheitsabstand:

```spot raum=durchgang start=1.68,2.63,-15
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    blick = spot.look(max_distance=1.2, start=0.6, margin=0.35)
    print("vorne:", blick.front.status)
    if blick.front.status == "clear":
        spot.move(forward=0.3)
    else:
        print("Zu eng, ich gehe nicht.")
```

Mit `margin=0.35` erkennt Spot, dass es vorne zu eng ist.

```quiz punkte=2
? Mit `margin=0.35` stösst Spot nicht mehr an. Warum setzt man den Sicherheitsabstand dann nicht gleich auf 1 m?
A) Weil `look` grössere Werte nicht annimmt.
B) Weil Spot dann langsamer geht.
C)* Weil dann auch Durchgänge als «blocked» gelten: Eine Tür von 90 cm lässt in der Mitte nur 45 cm Abstand zu jeder Seite, also käme Spot nie hindurch.
D) Weil der Sicherheitsabstand am echten Spot keine Wirkung hat.
! Der Sicherheitsabstand ist ein **Kompromiss**: Zu klein, und Spot streift Ecken. Zu gross, und er traut sich durch keine Tür. In einer 90 cm breiten Tür bleiben in der Mitte 45 cm zu jeder Seite. Mit `margin=0.35` darf der Strahl darum 10 cm neben der Mitte liegen. Mit `margin=0.4` sind es nur noch 5 cm, und Spot sucht lange, bis er die Lücke trifft. Mit `margin=0.5` kommt er gar nicht hindurch. Solche Zahlen findet man durch Nachdenken **und** Ausprobieren.
```

# Aufgabe: Durch die Tür

Spot soll ins rechte Zimmer finden. Er kennt den Plan nicht, er weiss nur: **Das andere Zimmer liegt im Osten** (Blick 0°). Drüben hängt ein AprilTag. Sobald Spot ihn sieht (`spot.tags()` ist nicht leer), ist er angekommen.

Diesmal läuft dein Programm **von vier Startplätzen gleichzeitig**. Ein fest einprogrammierter Weg funktioniert deshalb nicht — dein Programm muss wirklich hinschauen.

Ein Plan, der funktioniert: Wiederhole immer wieder:

1. Sieht Spot den Tag? Dann fertig.
2. Taste mit `direction` die Winkel von −90° bis 90° in Schritten von 10° ab.
3. Nimm unter den **freien** Richtungen die, die am nächsten bei Osten liegt.
4. Dreh dich dorthin und geh ein kurzes Stück (0.2 m).

So geht Spot nach Osten, solange es geht. Steht eine Wand im Weg, geht er an ihr entlang, bis die Tür frei wird.

```aufgabe raum=durchgang punkte=6 starts=1,3.2,0;1,0.8,0;3,2,90;3.5,3.3,180
ziel: ende_in 4.8 0.2 8.8 3.8
ziel: nicht_angestossen
ziel: ausgabe drüben
tipp: Wie weit eine Richtung von Osten abweicht: `abweichung = abs((blick.heading + winkel + 180) % 360 - 180)`. `blick.heading + winkel` ist die Richtung im Raum, und Osten ist 0°.
tipp: Stösst Spot irgendwo an? Dann ist der Sicherheitsabstand zu klein oder die Schritte sind zu lang. Sucht er ewig vor der Tür? Dann sind die Winkelschritte zu grob (nimm 10°) oder `margin` ist zu gross.
---
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    for schritt in range(100):
        if spot.tags():
            print("Ich sehe den Tag, ich bin drüben!")
            break
        blick = spot.look(max_distance=1.2, start=0.6, margin=0.35)
        # Welche freie Richtung liegt am nächsten bei Osten?
        bester_winkel = None

        # ... hier abtasten und auswählen ...

        if bester_winkel is None:
            spot.move(turn=90)       # nichts frei: umdrehen und neu schauen
        else:
            spot.move(turn=bester_winkel)
            spot.move(forward=0.2)
```
