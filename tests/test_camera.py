from gestes_webcam.camera import Horodateur


def test_horodatage_toujours_croissant():
    # MSMF peut livrer deux images à moins d'1 ms d'écart : MediaPipe refuse alors l'horodatage.
    h = Horodateur()
    vus = [h.ms(t) for t in (0.0, 0.0004, 0.0009, 0.033, 0.033, 0.010)]
    assert all(b > a for a, b in zip(vus, vus[1:]))
