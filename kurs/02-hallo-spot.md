---
nummer: 2
titel: Hallo Spot
---

# Das erste Programm

Jetzt bewegt sich Spot zum ersten Mal. Führe das Programm aus und schau rechts auf den Übungsraum: Spot ist das gelbe Rechteck, die schwarze Seite ist vorne (dort sitzen die Kameras).

```spot raum=leer
from spotlab import connect

with connect() as spot:
    spot.power_on()     # Motoren einschalten
    spot.stand()        # aufstehen
    print("Spot steht!")
    spot.sit()          # hinsetzen
```

Was passiert hier Zeile für Zeile?

- `from spotlab import connect` holt den Befehl `connect` aus spotlab. Ohne diese Zeile kennt Python ihn nicht.
- `with connect() as spot:` verbindet sich mit Spot. Ab jetzt heisst der Roboter in deinem Programm `spot`.
- Alle Zeilen, die darunter **eingerückt** sind (vier Leerzeichen), gehören zur Verbindung. Mit `spot.` davor gibst du Spot einen Befehl.

> Spot bewegt sich in diesem Programm nicht vom Fleck — er steht nur auf und setzt sich wieder hin. Auf der Karte siehst du deshalb noch keine Spur.

# Was der with-Block tut

Der `with`-Block ist mehr als eine Schreibweise. Wenn dein Programm am Ende des Blocks ankommt — oder vorher mit einem Fehler abbricht — räumt spotlab automatisch auf: Spot wird angehalten, die Motoren gehen aus und die Aufzeichnung wird gespeichert.

Das ist am echten Spot wichtig. Stell dir vor, dein Programm stürzt ab, während Spot läuft. Ohne Aufräumen liefe er mit dem letzten Befehl weiter.

```spot raum=leer fehler=ja
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    print("Gleich kommt ein Fehler ...")
    print(10 / 0)                       # Division durch null: Python bricht ab
    print("Diese Zeile kommt nie dran.")

print("Und diese auch nicht.")
```

Führe das Programm aus. Python meldet einen Fehler und hält an. spotlab hat Spot trotzdem sauber abgestellt, bevor das Programm endete.

```quiz punkte=1
? In welcher Zeile ist der Fehler, wenn du dieses Programm ausführst?
| from spotlab import connect
| with connect() as spot:
|     spot.power_on()
| spot.stand()
A) Zeile 2, weil der Doppelpunkt falsch ist
B) Zeile 3, weil `power_on` falsch geschrieben ist
C)* Zeile 4, weil `spot.stand()` nicht eingerückt ist und damit ausserhalb des with-Blocks steht
D) Es gibt keinen Fehler
! Zeile 4 ist nicht eingerückt. Für Python ist der `with`-Block nach Zeile 3 schon fertig, die Verbindung ist geschlossen. Spot kann dann keine Befehle mehr annehmen. Probiere es im Codefeld oben aus: nimm bei einer Zeile die Leerzeichen am Anfang weg und schau dir die Meldung an.
```

# Motoren und Haltung

Spot hat vier Grundbefehle für Motoren und Haltung:

- `spot.power_on()` schaltet die Motoren ein. Spot liegt dabei noch am Boden.
- `spot.stand()` lässt ihn aufstehen.
- `spot.sit()` lässt ihn hinsitzen (hinlegen).
- `spot.power_off()` setzt ihn hin und schaltet die Motoren aus.

Die Reihenfolge ist wichtig. Was passiert, wenn du sie vergisst? Probiere es aus:

```spot raum=leer fehler=ja
from spotlab import connect

with connect() as spot:
    spot.stand()
    print("steht")
```

Spot weigert sich. Lies die letzte Zeile der Fehlermeldung genau: spotlab sagt dir, was fehlt. Korrigiere das Programm, bis «steht» ausgegeben wird.

> Am echten Spot dauert `stand()` ungefähr zwei Sekunden. Dein Programm **wartet** in dieser Zeile, bis Spot wirklich steht, und macht erst dann weiter.

# Fehlermeldungen lesen

Fehlermeldungen sehen am Anfang erschreckend aus. Meistens brauchst du davon nur zwei Dinge:

1. **Die Zeilennummer in deinem Programm.** Der Kurs zeigt sie dir unter der Ausgabe in Rot an.
2. **Die letzte Zeile.** Dort steht, was schiefgegangen ist. Vor dem Doppelpunkt steht die Art des Fehlers, danach die Erklärung.

Die Zeilen dazwischen zeigen, durch welche Teile von spotlab der Fehler gewandert ist. Die brauchst du fast nie.

Ein paar Fehler, die oft vorkommen:

- `NameError: name 'spt' is not defined` — ein Name ist falsch geschrieben (hier `spt` statt `spot`).
- `AttributeError: 'Spot' object has no attribute 'stnd'` — den Befehl gibt es so nicht (hier `stnd` statt `stand`).
- `IndentationError` — die Einrückung stimmt nicht.
- `NotPowered: Die Motoren sind aus` — ein Spot-Befehl kam, bevor die Motoren an waren.

```quiz punkte=2
? Dein Programm bricht ab. Die letzte Zeile lautet: `AttributeError: 'Spot' object has no attribute 'power_ON'`. Was ist zu tun?
A) Die Motoren am Roboter von Hand einschalten
B) Python neu installieren
C) Vor `spot.power_ON()` noch `spot.stand()` schreiben
D)* `power_ON` klein schreiben: `spot.power_on()`
! Ein `AttributeError` heisst: Dieses Ding (hier `spot`) hat keinen Befehl mit diesem Namen. Python unterscheidet Gross- und Kleinschreibung, `power_ON` und `power_on` sind für Python zwei verschiedene Namen.
```

# Aufgabe: Spot begrüsst dich

Jetzt schreibst du selbst ein Programm. Unten steht ein Anfang. Ergänze es so, dass alle Punkte in der Liste erfüllt sind. Wenn du auf **Ausführen** drückst, prüft der Kurs dein Programm automatisch.

```aufgabe raum=leer punkte=3
ziel: aufgerufen stand
ziel: ausgabe Hallo, ich bin Spot
ziel: sitzt
tipp: Spot muss zuerst die Motoren einschalten, dann aufstehen. Am Ende soll er sitzen: dafür gibt es `spot.sit()`.
tipp: Die Ausgabe muss genau «Hallo, ich bin Spot» enthalten, mit Komma. Der Text steht bei print in Anführungszeichen.
---
from spotlab import connect

with connect() as spot:
    spot.power_on()
    # Spot soll aufstehen, «Hallo, ich bin Spot» ausgeben
    # und sich danach wieder hinsetzen.
```
