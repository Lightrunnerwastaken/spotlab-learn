from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    spot.move(forward=3.2)     # unter dem Tisch durch nach rechts
    spot.move(turn=90)
    spot.move(forward=1.55)    # rechts am Tisch vorbei nach oben
    spot.move(turn=90)         # Blick nach links (180°)
    spot.move(forward=1.1)     # in die Lücke
