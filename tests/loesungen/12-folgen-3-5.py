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
        if tags:
            p = ort_von(z, tags[0])
            if not spur or math.hypot(p[0] - spur[-1][0], p[1] - spur[-1][1]) > 0.2:
                spur.append(p)
        # 2. erreichte Punkte vorne streichen
        while len(spur) > 1 and math.hypot(spur[0][0] - z.x, spur[0][1] - z.y) < 0.3:
            spur.pop(0)
        if not spur:
            spot.stop()
            time.sleep(0.2)
            continue
        # 3. statt auf den Menschen auf den ersten Punkt der Spur lenken
        ziel, mensch = spur[0], spur[-1]
        dx, dy = ziel[0] - z.x, ziel[1] - z.y
        peilung = (math.degrees(math.atan2(dy, dx)) - z.heading + 180) % 360 - 180
        abstand = math.hypot(mensch[0] - z.x, mensch[1] - z.y)
        wunsch = WUNSCH if tags else 0.0       # unsichtbar: die Spur ganz abgehen
        drehen = max(-45, min(45, 1.2 * peilung))
        tempo = 0.0
        if abs(peilung) < 40 and abstand > wunsch:
            tempo = min(0.5, 0.6 * (abstand - wunsch))
        spot.walk(vx=tempo, wz=math.radians(drehen), duration=1.0, stop=False)
        time.sleep(0.2)
    spot.stop()
