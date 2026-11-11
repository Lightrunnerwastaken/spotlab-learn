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
        if spot.tags(id=5):
            z = spot.state
            tag = spot.tags(id=5)[0]
            richtung = math.radians(z.heading + tag.bearing)
            tag_x = z.x + tag.distance * math.cos(richtung)
            tag_y = z.y + tag.distance * math.sin(richtung)
            print(f"Tag 5 hängt bei x = {tag_x:.1f}, y = {tag_y:.1f}")
            break

        # 2. Das aktuelle Feld als besucht zählen.
        z = spot.state
        hier = feld(z.x, z.y)
        besuche[hier] = besuche.get(hier, 0) + 1

        # 3. Rundum schauen und die beste freie Richtung wählen.
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

        # 4. Dorthin drehen und 0.5 m gehen.
        if bester_winkel is None:
            spot.move(turn=90)
        else:
            spot.move(turn=bester_winkel)
            spot.move(forward=0.5)
