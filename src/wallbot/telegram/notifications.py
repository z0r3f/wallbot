import locale

import requests

from src.wallbot.config.constants import ICON_EXCLAMATION, ICON_DIRECT_HIT, ICON_COLLISION
from src.wallbot.config.settings import TELEGRAM_API_URL


def notel(chat_id, price, title, url_item, obs=None):
    # https://apps.timwhitlock.info/emoji/tables/unicode
    if obs is not None:
        text = ICON_EXCLAMATION
    else:
        text = ICON_DIRECT_HIT
    text += ' *' + title + '*'
    text += '\n'
    if obs is not None:
        text += ICON_COLLISION + ' '
    text += locale.currency(price, grouping=True)
    if obs is not None:
        text += obs
        text += ' ' + ICON_COLLISION
    text += '\n'
    text += 'https://es.wallapop.com/item/'
    text += url_item
    urlz0rb0t = TELEGRAM_API_URL + "sendMessage?chat_id=%s&parse_mode=markdown&text=%s" % (chat_id, text)
    requests.get(url=urlz0rb0t)
