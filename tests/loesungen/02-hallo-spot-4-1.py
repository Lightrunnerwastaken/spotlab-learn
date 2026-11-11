from spotlab import connect

with connect() as spot:
    spot.power_on()
    spot.stand()
    print("Hallo, ich bin Spot")
    spot.sit()
