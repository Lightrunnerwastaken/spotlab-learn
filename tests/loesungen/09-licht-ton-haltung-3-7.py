from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    # 1. blau
    spot.lights("blue", duration=1)
    # 2. Dreiklang
    for note in ["C", "E", "G"]:
        spot.beep(note, octave=5, duration=0.3)
    # 3. nicken
    spot.pose(pitch=15)
    spot.pose()
    # 4. grün, hinsetzen
    spot.lights("green", duration=1)
    spot.sit()
    print("Begrüssung fertig")
