import glob
import os

import segno
from segno import helpers

card_data = {
    "name": "Walsh, Wyatt",
    "displayname": "Wyatt Walsh",
    "email": "wyattowalsh@gmail.com",
    "cellphone": "2096022545",
    "url": ["https://www.w4w.dev/", "https://www.linkedin.com/in/wyattowalsh", "https://www.github.com/wyattowalsh"]
}


def get_qr_code(data):
    card = helpers.make_vcard_data(**card_data)
    qrcode = segno.make(card, error='H')
    qrcode.to_artistic(background="assets/logo.png", target='assets/qr.png', scale=25)


if __name__ == "__main__":
    get_qr_code(card_data)