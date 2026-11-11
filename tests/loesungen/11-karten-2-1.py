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
    z = spot.state
    wegpunkte.append((z.x, z.y))

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
            z = spot.state
            wegpunkte.append((z.x, z.y))

    # Über die Wegpunkte zurück zum Start
    for x, y in reversed(wegpunkte):
        gehe_zu(spot, x, y)
