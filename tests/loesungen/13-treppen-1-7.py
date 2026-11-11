import time
from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    t = spot.stairs()[0]
    unten = spot.state.z
    spot.move(turn=t.axis_bearing)              # Nase bergauf
    while spot.state.z - unten < t.rise_m - 0.05:
        spot.walk(vx=0.25, duration=1.0, stop=False)
        time.sleep(0.2)
    spot.walk(vx=0.25, duration=1.5)

    # oben: welchen Tag siehst du?
    tags = spot.tags()
    print(f"Tag {tags[0].id}")

    # rückwärts hinunter, bis die Körperhöhe wieder unten ist
    while spot.state.z - unten > 0.05:
        spot.walk(vx=-0.25, duration=1.0, stop=False)
        time.sleep(0.2)
    spot.walk(vx=-0.25, duration=1.0)

    # hinsetzen
    spot.sit()
