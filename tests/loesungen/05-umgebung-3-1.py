from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    while spot.look(max_distance=1.0, start=0.6).front.status == "clear":
        spot.move(forward=0.25)
    print("Wand erreicht")
