import locale
import logging
import requests
import telebot

from src.wallbot.config.constants import ICON_COLLISION, ICON_DIRECT_HIT, ICON_EXCLAMATION
from src.wallbot.config.settings import APP_VERSION, AUTHORIZED_USERS, TELEGRAM_API_URL


def _escape_markdown(text: str) -> str:
    """Escapa caracteres básicos que rompen el Markdown estándar de Telegram."""
    if not text:
        return ""
    # Reemplaza caracteres que pueden desemparejar el formateo
    return text.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`").replace("[", "\\[")


def notel(chat_id, price, title, url_item, obs=None):
    """Envía la notificación de un nuevo anuncio encontrado en Wallapop."""
    safe_title = _escape_markdown(title)
    icon_main = ICON_EXCLAMATION if obs is not None else ICON_DIRECT_HIT
    text_lines = [f"{icon_main} *{safe_title}*"]

    # Formateo seguro del precio
    try:
        numeric_price = float(price)
        formatted_price = locale.currency(numeric_price, grouping=True)
    except (ValueError, TypeError):
        formatted_price = f"{price} €"

    # Inclusión de observaciones si existen
    if obs is not None:
        text_lines.append(f"{ICON_COLLISION} {formatted_price} {obs} {ICON_COLLISION}")
    else:
        text_lines.append(formatted_price)

    text_lines.append(f"https://es.wallapop.com/item/{url_item}")
    message_text = "\n".join(text_lines)

    send_url = f"{TELEGRAM_API_URL}sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }

    try:
        response = requests.post(send_url, json=payload, timeout=10)
        if not response.ok:
            # Imprime el motivo exacto que devuelve la API de Telegram en JSON
            logging.error(
                "Error al enviar notificación a Telegram (Chat ID: %s): %s - %s",
                chat_id,
                response.status_code,
                response.text,
            )
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        logging.error("Excepción en envío a Telegram (Chat ID: %s): %s", chat_id, err)


def notify_startup(bot: telebot.TeleBot):
    """Envía un mensaje de inicio con la versión únicamente al primer usuario (admin)."""
    if not AUTHORIZED_USERS:
        return

    admin_user = AUTHORIZED_USERS[0]

    if admin_user.isdigit() or (admin_user.startswith("-") and admin_user[1:].isdigit()):
        message = f"🚀 *Wallbot iniciado* `v{APP_VERSION}`"
        try:
            bot.send_message(chat_id=int(admin_user), text=message, parse_mode="Markdown")
            logging.info("Notificación de arranque enviada al admin ID: %s", admin_user)
        except Exception as e:
            logging.warning("No se pudo enviar notificación de inicio al admin %s: %s", admin_user, e)
    else:
        logging.warning(
            "El primer usuario en AUTHORIZED_USERS (%s) no es un Chat ID numérico válido.",
            admin_user,
        )
