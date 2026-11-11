import numpy as np
from spotlab import connect


def frei_bis(spot):
    punkte = np.vstack([
        spot.point_cloud("frontleft", frame="body").points,
        spot.point_cloud("frontright", frame="body").points,
    ])
    ueber_boden = punkte[punkte[:, 2] > -0.4]
    vor_mir = ueber_boden[np.abs(ueber_boden[:, 1]) < 0.35]
    if len(vor_mir) == 0:
        return None
    return vor_mir[:, 0].min()


with connect() as spot:
    abstand = frei_bis(spot)
    if abstand is None:
        print("Vorne bis 4 m nichts gesehen")
    else:
        print(f"Frei bis {abstand:.1f} m")
