"""Génère empaqueter/gestes.ico (et une version PNG pour le site) à partir de l'icône de l'app."""
from pathlib import Path
import sys

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent))

from PIL import Image, ImageDraw  # noqa: E402


def grande(actif=True, taille=256):
    """Même dessin que appli.image_icone, à la taille voulue."""
    s = taille / 64 * 4
    img = Image.new("RGBA", (int(64 * s), int(64 * s)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    S = lambda *v: tuple(round(x * s) for x in v)
    d.rounded_rectangle(S(2, 2, 62, 62), radius=round(14 * s), fill=(46, 49, 58, 255))
    blanc = (255, 255, 255, 255)
    for x, haut in ((20, 16), (27, 12), (34, 12), (41, 16)):
        d.rounded_rectangle(S(x, haut, x + 5, 38), radius=round(3 * s), fill=blanc)
    d.rounded_rectangle(S(12, 30, 17, 42), radius=round(3 * s), fill=blanc)
    d.rounded_rectangle(S(17, 30, 46, 52), radius=round(8 * s), fill=blanc)
    couleur = (52, 199, 140, 255) if actif else (140, 144, 156, 255)
    d.ellipse(S(42, 42, 60, 60), fill=couleur, outline=(46, 49, 58, 255), width=round(3 * s))
    return img.resize((taille, taille), Image.LANCZOS)


if __name__ == "__main__":
    img = grande(taille=256)
    img.save(ICI / "gestes.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    try:   # macOS : l'icône de Gestes.app
        img_mac = grande(taille=1024)
        img_mac.save(ICI / "gestes.icns")
    except Exception as e:
        print("icns non créé :", e)
    site = ICI.parent / "site" / "img"
    site.mkdir(parents=True, exist_ok=True)
    grande(taille=512).save(site / "icone.png")
    grande(taille=64).save(site / "favicon.png")
    print("icône OK")
