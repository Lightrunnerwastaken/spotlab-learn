---
nummer: 10
titel: Kameras und Tiefe
---

# Ein Kamerabild holen

Spot hat **fünf Kameras**: zwei vorne, je eine links und rechts und eine hinten. Jede davon liefert zwei Bilder: ein gewöhnliches Graubild und ein **Tiefenbild**, das für jeden Bildpunkt sagt, wie weit weg er ist. Aus den Tiefenbildern baut Spot das Hindernisgitter, das du seit Kapitel 5 mit `look()` benutzt.

Der 2D-Übungsraum hat keine Kameras. Die Bilder in diesem Kapitel stammen deshalb aus spotlabs **3D-Übungsraum**: Dort wurde Spot an eine feste Stelle gestellt, und für jede Kamera wurde die Antwort gespeichert, die ein Roboter schickt. Dein Programm bekommt genau diese Antworten. Darum **steht Spot in diesem Kapitel still**. Nach einem Schritt würden die Bilder nicht mehr stimmen, und spotlab verweigert ihn.

Spot steht im Raum «Möbliert» vor dem Tisch. Alles, was dein Programm als PNG-Datei speichert, erscheint unter der Ausgabe.

```spot raum=kamera-tisch
from spotlab import connect

with connect() as spot:
    print("Kameras:", spot.cameras())
    for name in ["frontleft", "frontright"]:
        bild = spot.camera(name)
        print(name, bild.width, "x", bild.height)
        bild.save(name + ".png")
```

`spot.camera(name)` gibt ein **Bild-Objekt** zurück. `bild.save("name.png")` speichert es. `frontleft` schaut nach vorne links, `frontright` nach vorne rechts, beide schräg nach unten. Zusammen zeigen sie, was vor Spot liegt: jede eine Hälfte des Tischs.

> Die Bilder hier sind **gerendert**, also gezeichnet und nicht fotografiert. Am echten Spot sehen sie anders aus (Fischaugen-Objektiv, Licht, Rauschen), die Befehle sind aber dieselben.

## Ein Bild ist eine Tabelle aus Zahlen

`bild.array` ist das Bild als **numpy-Array**: eine Tabelle mit 480 Zeilen und 640 Spalten. Jeder Eintrag ist die Helligkeit eines Bildpunkts, von 0 (schwarz) bis 255 (weiss).

```spot raum=kamera-tisch
from spotlab import connect

with connect() as spot:
    a = spot.camera("frontleft").array
    print("Form:", a.shape)
    print("Pixel in der Mitte:", a[240, 320])
    print("Pixel oben links:", a[0, 0])
    print("mittlere Helligkeit:", round(a.mean(), 1))
```

Achtung bei der Reihenfolge: `a[zeile, spalte]`. Zuerst kommt, wie weit **unten**, dann, wie weit **rechts**. Die Zeile 0 ist ganz oben.

```quiz punkte=2
? Du willst den Bildpunkt, der **100 Pixel vom linken Rand** und **50 Pixel vom oberen Rand** entfernt ist. Was schreibst du?
A) `a[100, 50]`
B)* `a[50, 100]`
C) `a[100][50]`
D) `a[-50, 100]`
! numpy fragt zuerst nach der Zeile (von oben gezählt), dann nach der Spalte (von links gezählt). 50 von oben ist Zeile 50, 100 von links ist Spalte 100. Das ist umgekehrt wie bei Koordinaten (x, y), und genau darum ist es ein häufiger Fehler. `a[100][50]` (C) wäre dasselbe wie A.
```

# Das Tiefenbild in Metern

Jetzt steht Spot im Raum «Durchgang» vor der Tür ins andere Zimmer. `spot.depth(name)` holt das **Tiefenbild** einer Kamera:

```spot raum=kamera-tuer
import numpy as np
from PIL import Image
from spotlab import connect

with connect() as spot:
    t = spot.depth("frontleft")
    print("Form:", t.meters.shape)
    print("Mitte:", t.distance_at(212, 120), "m")
    print("gültig:", round(t.valid.mean() * 100), "%")
    print("nächster Punkt:", round(t.meters[t.valid].min(), 2), "m")

    # Als Bild: nah = hell, weit = dunkel, ohne Messung = schwarz
    m = np.clip(np.nan_to_num(t.meters), 0, 4)
    hell = np.where(t.valid, 60 + 195 * (1 - m / 4), 0).astype(np.uint8)
    Image.fromarray(hell).save("tiefe.png")
```

Das Tiefenbild hat drei wichtige Teile:

- `t.meters`: für jeden Bildpunkt die Tiefe in Metern. Gemeint ist der Abstand **in Blickrichtung der Kamera**, nicht der direkte Abstand.
- `t.valid`: für jeden Bildpunkt `True` oder `False`, ob es überhaupt eine Messung gibt.
- `t.distance_at(spalte, zeile)`: ein einzelner Punkt in Metern, oder `None`, wenn es dort keine Messung gibt. Hier kommt die **Spalte zuerst**, anders als bei `a[zeile, spalte]`.

Im Bild `tiefe.png` siehst du einen schwarzen Bereich: Das ist die Tür. Hinter ihr liegt das andere Zimmer, und das ist weiter weg, als die Tiefenkamera misst (im Übungsraum 4 m). Dort gibt es keine Messung. Das heisst **nicht**, dass dort nichts ist. Es heisst nur: Spot weiss es nicht.

Mit `from PIL import Image` holst du das Bildpaket Pillow. `Image.fromarray(feld).save(...)` macht aus jedem Zahlenfeld mit Werten von 0 bis 255 ein Bild.

```quiz punkte=2
? `t.distance_at(300, 100)` gibt `None` zurück. Was weisst du über diese Stelle?
A) Dort ist nichts, Spot kann frei dorthin gehen.
B) Dort steht ein Hindernis direkt vor der Kamera, Abstand 0.
C)* Spot hat dort keine gültige Messung. Es kann zu weit weg sein, oder die Kamera sieht die Oberfläche nicht. Ob frei ist, weiss er nicht.
D) Die Pixelkoordinaten sind ausserhalb des Bildes.
! `None` heisst «keine Messung», mit Absicht nicht 0. Eine 0 sähe aus wie «Hindernis direkt vor der Nase», und ein Programm, das mit den Zahlen rechnet, würde sie still mitverwenden. D gibt es auch (dann kommt ebenfalls `None`), aber (300, 100) liegt im Bild: Es ist 424 Spalten breit und 240 Zeilen hoch. Am echten Spot kommt eine wichtige Ursache dazu: **Glas**. Die Tiefenkameras sehen durch Glas hindurch, als wäre es nicht da.
```

# Punktwolken

Ein Tiefenbild sagt, wie weit jeder Bildpunkt **von der Kamera** weg ist. Spot will aber wissen, wo die Punkte **relativ zu sich selbst** liegen. `spot.point_cloud(name, frame="body")` rechnet jeden gültigen Bildpunkt in einen Punkt im Raum um, mit drei Zahlen in Metern:

- **x**: nach vorne
- **y**: nach links
- **z**: nach oben

Der Nullpunkt ist die Mitte von Spots Körper. Der Boden liegt im Übungsraum bei z ≈ −0.52 m, denn der Körper ist so hoch über dem Boden.

Spot steht wieder vor dem Tisch. Wie weit ist der Weg geradeaus frei?

```spot raum=kamera-tisch
import numpy as np
from spotlab import connect

with connect() as spot:
    punkte = np.vstack([
        spot.point_cloud("frontleft", frame="body").points,
        spot.point_cloud("frontright", frame="body").points,
    ])
    print("Punkte:", len(punkte))

    ueber_boden = punkte[punkte[:, 2] > -0.4]
    vor_mir = ueber_boden[np.abs(ueber_boden[:, 1]) < 0.35]
    print("Punkte vor mir:", len(vor_mir))
    print(f"Frei bis {vor_mir[:, 0].min():.2f} m")
```

So arbeitet das Programm:

1. `.points` ist ein Array mit einer Zeile je Punkt und drei Spalten (x, y, z). `np.vstack` legt die Punkte beider Kameras zusammen.
2. `punkte[:, 2] > -0.4` fragt für jeden Punkt: Liegt er höher als 40 cm unter der Körpermitte, also deutlich über dem Boden? Das Ergebnis ist eine Liste aus `True`/`False`, und `punkte[...]` behält nur die Zeilen mit `True`.
3. `np.abs(...[:, 1]) < 0.35` behält nur, was in einem 70 cm breiten **Gang** vor Spot liegt. Spot ist gut 50 cm breit, dazu kommt ein Rand.
4. Der kleinste x-Wert im Gang ist das nächste Hindernis.

Das Ergebnis, 1.3 m, passt zur Karte: Spot steht bei x = 1.2, die Tischkante liegt bei x = 2.5.

```quiz punkte=2
? Was gibt das Programm aus, wenn du die Zeile `ueber_boden = punkte[punkte[:, 2] > -0.4]` weglässt (und mit allen Punkten weiterrechnest)?
A) Dasselbe, 1.30 m: der Boden ist ja kein Hindernis.
B)* Etwa 0.6 m: Der nächste Punkt ist dann der Boden direkt vor Spot.
C) Eine Fehlermeldung, weil die Punktwolke leer ist.
D) Einen grösseren Wert, weil mehr Punkte den Durchschnitt verschieben.
! Die Kameras schauen schräg nach unten, und die meisten Punkte liegen **auf dem Boden**, die nächsten nur gut einen halben Meter vor Spot. Ohne den Höhenfilter hielte das Programm den Boden für ein Hindernis. Darum trennt man zuerst Boden und Nicht-Boden. Spot selbst macht dasselbe, wenn er aus den Tiefenbildern sein Hindernisgitter baut.
```

# Bilder auswerten

## Aufgabe 1: Der Hinderniswächter

Schreib eine Funktion `frei_bis(spot)`. Sie soll mit den Punktwolken der beiden vorderen Kameras ausrechnen, wie weit der 70 cm breite Gang vor Spot frei ist, und diese Zahl zurückgeben. Das Programm gibt dann genau so aus:

`Frei bis 1.3 m` (eine Stelle nach dem Komma)

```aufgabe raum=kamera-tisch punkte=4
ziel: ausgabe Frei bis 1.3 m
ziel: aufgerufen depth
tipp: Alles, was du brauchst, steht im Beispiel bei «Punktwolken». Pack es in eine Funktion, die am Ende `return vor_mir[:, 0].min()` macht.
tipp: Eine Stelle nach dem Komma: `print(f"Frei bis {abstand:.1f} m")`.
---
import numpy as np
from spotlab import connect


def frei_bis(spot):
    # Punktwolken der beiden vorderen Kameras holen, Boden weg, Gang behalten,
    # und den kleinsten x-Wert zurückgeben
    pass


with connect() as spot:
    abstand = frei_bis(spot)
    print(f"Frei bis {abstand:.1f} m")
```

## Aufgabe 2: Und vor der Tür?

Jetzt steht Spot vor der Tür im Raum «Durchgang». Der Startcode ist eine Lösung von Aufgabe 1, und hier stürzt er ab. Warum? Im Gang vor Spot gibt es **keinen einzigen Punkt**: Durch die Tür sieht er weiter, als die Tiefenkamera misst.

Ändere das Programm: Wenn im Gang kein Punkt liegt, gibt `frei_bis` den Wert `None` zurück, und das Programm sagt dann ehrlich `Vorne bis 4 m nichts gesehen`. Sonst wie bisher `Frei bis ... m`. Dein Programm soll in **beiden** Szenen das Richtige sagen: Probier es danach in Aufgabe 1 aus.

```aufgabe raum=kamera-tuer punkte=4
ziel: ausgabe Vorne bis 4 m nichts gesehen
ziel: aufgerufen depth
tipp: Wie viele Punkte im Gang liegen, sagt `len(vor_mir)`. Ist das 0, gib `None` zurück.
tipp: Beim Ausgeben: `if abstand is None: ... else: ...`
---
import numpy as np
from spotlab import connect


def frei_bis(spot):
    punkte = np.vstack([
        spot.point_cloud("frontleft", frame="body").points,
        spot.point_cloud("frontright", frame="body").points,
    ])
    ueber_boden = punkte[punkte[:, 2] > -0.4]
    vor_mir = ueber_boden[np.abs(ueber_boden[:, 1]) < 0.35]
    return vor_mir[:, 0].min()


with connect() as spot:
    abstand = frei_bis(spot)
    print(f"Frei bis {abstand:.1f} m")
```

«Nichts gesehen» ist nicht dasselbe wie «frei». Ein Roboter, der beides verwechselt, fährt in eine Glastür. Darum unterscheidet spotlab überall zwischen «frei», «blockiert» und «unbekannt», bei `look()` genauso wie hier.
