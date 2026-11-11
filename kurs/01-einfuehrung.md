---
nummer: 1
titel: Einführung
---

# Herzlich willkommen

In diesem Kurs lernst du, **Spot** zu programmieren — den vierbeinigen Roboter von Boston Dynamics, der bei uns in der Schule steht.

Du schreibst dafür Programme in **Python**. Damit du nicht zuerst Hunderte Seiten Anleitung lesen musst, benutzt du **spotlab**: eine Sammlung von Befehlen, die wir für den Unterricht gebaut haben. Mit spotlab reichen fünf Zeilen, damit Spot aufsteht und ein paar Schritte geht.

Am Ende des Kurses kannst du eigene Projekte umsetzen, zum Beispiel:

- Spot erkundet einen Raum, den er noch nie gesehen hat, ohne an etwas anzustossen.
- Spot sucht ein bestimmtes Objekt (einen AprilTag) und bleibt davor stehen.
- Spot nimmt eine Karte auf und findet später selbst den Weg zu einem Ort darauf.
- Spot folgt einem Menschen.

> **So ist der Kurs gebaut:** Du liest kurz, probierst sofort aus und beantwortest dann Fragen. Die Fragen prüfen nicht, ob du dir etwas gemerkt hast, sondern ob du es **anwenden** kannst. Oft lohnt es sich, vor dem Antworten den Code selbst auszuprobieren.

# Spot, spotlab und der Simulator

Ein echter Roboter ist teuer, schwer und kann Menschen verletzen. Deshalb übst du zuerst im **Simulator**: einem Programm, das so tut, als wäre Spot da. Dein Code ist genau derselbe wie am echten Roboter.

## Die drei Teile

- **Spot** ist der Roboter. Er hat Motoren in den Beinen, Kameras rundherum und einen eigenen Computer, der für ihn das Gleichgewicht hält. Du sagst ihm nicht, wie er jedes Bein bewegen soll, sondern zum Beispiel «geh einen Meter nach vorne».
- **spotlab** ist die Python-Bibliothek, mit der du Spot Befehle gibst. Sie kümmert sich im Hintergrund um alles Lästige: Anmelden, Not-Aus, Aufzeichnen.
- **Der Simulator** ersetzt den echten Spot. In diesem Kurs läuft er in einem Übungsraum, den du rechts neben der Ausgabe von oben siehst.

## Was der Simulator nicht kann

Der Simulator rechnet keine echte Physik: Spot kann darin nicht umfallen oder ausrutschen. Er weiss aber, wo Wände und Möbel stehen, und merkt, wenn Spot anstösst. Kameras, Licht und Ton gibt es darin nicht — die probierst du später am echten Roboter aus.

```quiz punkte=1
? Dein Programm läuft im Simulator fehlerfrei durch. Was weisst du damit über den echten Spot?
A) Es läuft am echten Spot sicher genauso, denn der Code ist derselbe.
B)* Die Befehle und die Reihenfolge stimmen. Ob Spot am echten Ort zum Beispiel ausrutscht oder ein Hindernis anders liegt, weisst du noch nicht.
C) Nichts, der Simulator hat mit dem echten Spot nichts zu tun.
D) Dass Spot nirgends anstossen kann, denn der Simulator hätte es gemerkt.
! Der Simulator prüft deinen **Ablauf**: richtige Befehle, richtige Reihenfolge, keine Fehler im Code. Die echte Welt ist aber nie genau gleich wie der Übungsraum: Möbel stehen anders, der Boden ist rutschig, ein Mensch läuft vorbei. Darum testet man am echten Roboter immer zuerst langsam und mit jemandem am Not-Aus.
```

# So funktioniert dieser Kurs

Unten siehst du ein Codefeld. Klicke auf **Ausführen** (oder drücke Strg+Enter). Die Ausgabe erscheint im dunklen Feld darunter.

```spot raum=keiner
# Alles nach einem # ist ein Kommentar: Python überspringt es.
print("Hallo Spot!")
print("Spot hat", 4, "Beine")
print("Zwei Spots haben", 2 * 4, "Beine")
```

Du kannst den Code ändern und neu ausführen, so oft du willst. Deine Änderungen bleiben gespeichert, auch wenn du die Seite verlässt. Mit dem Pfeil im Kreis holst du den ursprünglichen Code zurück, mit dem Pfeil nach unten speicherst du ihn als Datei.

Probiere es aus: Ändere die letzte Zeile so, dass sie ausrechnet, wie viele Beine **sieben** Spots haben.

```quiz punkte=1
? Was gibt diese Zeile aus? `print("Spot", "wiegt", 32, "kg")`
A) `Spot wiegt 32 kg` und dazu die Anführungszeichen
B) `Spot,wiegt,32,kg`
C)* `Spot wiegt 32 kg`
D) Einen Fehler, weil Wörter und Zahlen gemischt sind
! `print` schreibt alles, was du ihm mit Kommas getrennt gibst, nacheinander hin — mit **einem Leerzeichen** dazwischen. Die Anführungszeichen gehören nicht zum Text, sie zeigen Python nur, wo der Text anfängt und aufhört. Wörter und Zahlen darfst du bei `print` mischen.
```

# Sicherheit am echten Spot

Spot wiegt etwa 32 kg und läuft bis zu 1.6 m pro Sekunde. Ein Programmfehler kann ihn gegen eine Wand oder einen Menschen laufen lassen. Darum gelten am echten Roboter feste Regeln:

1. **Es steht immer jemand am Not-Aus.** Der Not-Aus nimmt Spot sofort die Kraft aus den Motoren, egal was dein Programm gerade tut.
2. **Niemand steht im Weg.** Halte mindestens zwei Meter Abstand, solange Spot steht oder läuft.
3. **Erst im Simulator, dann echt.** Jedes Programm läuft zuerst hier.
4. **Klein anfangen.** Am echten Spot zuerst kurze Strecken und langsame Geschwindigkeiten.

> spotlab hilft dir dabei: Wer nichts einstellt, fährt nie den echten Spot, sondern immer den Simulator. Und dieser Kurs kann den echten Spot gar nicht erreichen, auch wenn du es im Code versuchst.

```quiz punkte=1
? Am echten Spot startest du ein neues Programm. Spot läuft los, aber anders als gedacht: er geht direkt auf ein Pult zu. Was tust du zuerst?
A) Schnell den Code ändern und das Programm neu starten
B) Spot festhalten, damit er nicht gegen das Pult läuft
C)* Den Not-Aus drücken (oder rufen, dass die Person am Not-Aus ihn drückt)
D) Abwarten, Spot erkennt Hindernisse ja selbst
! Der Not-Aus ist immer der erste Schritt, wenn etwas anders läuft als geplant. Code ändern dauert zu lange, und einen 32-kg-Roboter festzuhalten ist gefährlich. Spot hat zwar eine eigene Hinderniserkennung, aber du kannst dich nicht darauf verlassen — zum Beispiel sieht er Glas schlecht.
```
