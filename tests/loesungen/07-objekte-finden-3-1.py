import math
from spotlab import connect

def gehe_zu(spot, x, y):
    z = spot.state
    dx = x - z.x
    dy = y - z.y
    richtung = math.degrees(math.atan2(dy, dx))
    drehung = (richtung - z.heading + 180) % 360 - 180
    spot.move(turn=drehung)
    spot.move(forward=math.hypot(dx, dy))

with connect() as spot:
    spot.power_on()
    spot.stand()

    # 1. Suchen, bis Tag 1 zu sehen ist
    schritte = 0
    while not spot.tags(id=1) and schritte < 10:
        spot.move(forward=0.5)
        schritte += 1

    # 2. Ausrechnen, wo Tag 1 hängt
    z = spot.state
    tag = spot.tags(id=1)[0]
    richtung = math.radians(z.heading + tag.bearing)
    tag_x = z.x + tag.distance * math.cos(richtung)
    tag_y = z.y + tag.distance * math.sin(richtung)

    # 3. Zum Punkt 0.8 m vor dem Tag gehen
    gehe_zu(spot, tag_x - 0.8, tag_y)

    # 4. Zum Tag drehen
    spot.move(turn=(0 - spot.state.heading + 180) % 360 - 180)

    print("Vor Tag 1 angekommen.")
