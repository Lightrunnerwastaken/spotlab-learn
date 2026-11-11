from spotlab import connect

OSTEN = 0

with connect() as spot:
    spot.power_on()
    spot.stand()
    for schritt in range(100):
        if spot.tags():
            print("Ich sehe den Tag, ich bin drüben!")
            break
        blick = spot.look(max_distance=1.2, start=0.6, margin=0.35)
        bester_winkel, beste_abweichung = None, 999
        for winkel in range(-90, 91, 10):
            if blick.direction(winkel).status == "clear":
                abweichung = abs((blick.heading + winkel - OSTEN + 180) % 360 - 180)
                if abweichung < beste_abweichung:
                    bester_winkel, beste_abweichung = winkel, abweichung
        if bester_winkel is None:
            spot.move(turn=90)
        else:
            if bester_winkel != 0:
                spot.move(turn=bester_winkel)
            spot.move(forward=0.2)
