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
    for x, y in [(3, 1), (3, 3), (1, 3), (1, 1)]:
        gehe_zu(spot, x, y)
    print("Rundgang fertig")
