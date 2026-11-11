from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    licht = spot.supports("lights")
    ton = spot.supports("beep")
    haltung = spot.supports("pose")
    if licht:
        spot.lights("blue", duration=1)
    if ton:
        for note in ["C", "E", "G"]:
            spot.beep(note, octave=5, duration=0.3)
    if haltung:
        spot.pose(pitch=15)
        spot.pose()
    if licht:
        spot.lights("green", duration=1)
    spot.sit()
    print("Begrüssung fertig")
