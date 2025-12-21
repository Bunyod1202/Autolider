import hashlib
from time import sleep

from django.utils import timezone
from requests import post
from telebot import TeleBot, types
from telebot.apihelper import ApiException

from users.models import User
from bot.models import Constant
from bot import models as bot_models
from bot.utils.constants import TOKEN
from threading import Thread

from bot.utils.constants import CONSTANT, BASE_URL


def is_phone_number(raw: str):
    if any([
        all([raw.startswith("+998"), raw[1:].isdigit(), len(raw) == 13]),
        all([raw.startswith("998"), raw.isdigit(), len(raw) == 12]),
        all([raw.isdigit(), len(raw) == 9])
    ]):
        return True
    return False


def normalize_phone_number(raw: str) -> str:
    """Return phone in +998XXXXXXXXX format when possible; else empty string."""
    if not raw:
        return ''
    s = ''.join(ch for ch in str(raw).strip() if ch.isdigit() or ch == '+')
    if s.startswith('+998') and len(s) == 13 and s[1:].isdigit():
        return s
    if s.startswith('998') and len(s) == 12 and s.isdigit():
        return '+{}'.format(s)
    if s.startswith('+') and not s.startswith('+998') and s[1:].isdigit():
        # Non-UZ, store as-is
        return s
    digits = ''.join(ch for ch in s if ch.isdigit())
    if len(digits) == 9:  # e.g. 901234567
        return '+998' + digits
    if len(digits) == 12 and digits.startswith('998'):
        return '+' + digits
    return ''


def upload_file(bot, file_id):
    downloaded_file = bot.download_file(bot.get_file(file_id).file_path)
    file_path = post('https://telegra.ph/upload', files={'file': ('file', downloaded_file, 'image/jpeg')}).json()[0]['src']
    return f"https://telegra.ph{file_path}"


def get_keyboard_markup(buttons, on_time=True):
    keyboard_markup = types.ReplyKeyboardMarkup(True, on_time)
    for row in buttons:
        if type(row) is list:
            keyboard_markup.add(*[types.KeyboardButton(button, request_contact=True if button.startswith("📞 ") else None) for button in row])
        else:
            keyboard_markup.add(types.KeyboardButton(row, request_contact=True if row.startswith("📞 ") else None))
    return keyboard_markup


def get_main_keyboard_markup(user):
    keyboard_markup = types.ReplyKeyboardMarkup(True, False)
    keyboard_markup.add(
        types.KeyboardButton(
            user.text.tests,
            web_app=types.WebAppInfo(
                url=f"{BASE_URL}/bot/themes/?user_id={user.id}"
            ),
        ),
    )
    # Conditionally show Exams button only if user has phone and admin granted access
    try:
        from tests.models import ExamAccess
        has_access = bool(user.phone_number) and ExamAccess.objects.filter(user=user, exam__is_active=True).exists()
        if has_access:
            keyboard_markup.add(
                types.KeyboardButton(user.text.exams)
            )
    except Exception:
        # If exams not set up yet, ignore silently
        pass
    keyboard_markup.add(
        types.KeyboardButton(
            user.text.subscription,
        ),
    )
    keyboard_markup.add(
        types.KeyboardButton(
            user.text.comment,
        ),
        types.KeyboardButton(
            user.text.help,
            web_app=types.WebAppInfo(
                url=f"{BASE_URL}/bot/help/?user_id={user.id}"
            ),
        ),
    )
    keyboard_markup.add(
        types.KeyboardButton(
            user.text.change_language,
        ),
    )
    return keyboard_markup


def extract_full_name(message: types.Message):
    return f"{message.from_user.first_name}{f' {message.from_user.last_name}' if message.from_user.last_name else ''}"


def get_new_token(salt):
    md5 = hashlib.md5()
    md5.update(f"{timezone.now().microsecond * 1.24213}{salt}".encode())
    return md5.hexdigest()


def get_constant(key):
    constant, created = Constant.objects.get_or_create(key=key, defaults={'data': CONSTANT.DEFAULT.get(key)})
    return constant.actual_data


def sending_post(bot: TeleBot, message: types.Message, sender: User):
    total = 0
    users = list(User.objects.all())
    for user in users:
        try:
            if message.audio:
                bot.send_audio(
                    user.telegram_id,
                    message.audio.file_id,
                    caption=message.html_caption,
                    reply_markup=message.reply_markup
                )
            elif message.voice:
                bot.send_voice(
                    user.telegram_id,
                    message.voice.file_id,
                    caption=message.html_caption,
                    reply_markup=message.reply_markup
                )
            elif message.video:
                bot.send_video(
                    user.telegram_id,
                    message.video.file_id,
                    caption=message.html_caption,
                    reply_markup=message.reply_markup
                )
            elif message.photo:
                bot.send_photo(
                    user.telegram_id,
                    message.photo[-1].file_id,
                    caption=message.html_caption,
                    reply_markup=message.reply_markup
                )
            else:
                bot.send_message(
                    user.telegram_id,
                    message.html_text,
                    reply_markup=message.reply_markup
                )
            total += 1
            sleep(0.05)
        except ApiException as e:
            error = str(e.args)
            if "deactivated" in error or "blocked by the user" in error:
                user.is_active = False
                user.save()
                continue
            else:
                users.append(user)
    bot.send_message(
        sender.telegram_id,
        sender.text.posting_end.format(
            user_counts=len(users),
            total=total
        )
    )


def broadcast_announcement(bot: TeleBot, title: str, text: str = None, photo_file=None, video_file=None,
                           button_text: str = None, button_url: str = None):
    """
    Send an announcement to all users with optional media and single URL button.
    `photo_file` / `video_file` should be file-like objects opened in binary mode.
    """
    markup = None
    if button_text and button_url:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text=button_text, url=button_url))

    users = list(User.objects.all())
    total = 0
    for user in users:
        try:
            if video_file is not None:
                bot.send_video(user.telegram_id, video_file, caption=text or None, reply_markup=markup)
            elif photo_file is not None:
                bot.send_photo(user.telegram_id, photo_file, caption=text or None, reply_markup=markup)
            else:
                bot.send_message(user.telegram_id, text or title, reply_markup=markup)
            total += 1
            sleep(0.05)
        except ApiException as e:
            error = str(e.args)
            if "deactivated" in error or "blocked by the user" in error:
                user.is_active = False
                user.save(update_fields=["is_active"])
                continue
            else:
                # best-effort, skip on other API errors
                continue
    return total


def _build_inline_markup(button_text: str = None, button_url: str = None):
    if button_text and button_url:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text=button_text, url=button_url))
        return markup
    return None


def send_announcement_in_background(announcement_id: int):
    """Background sender for Announcement to avoid request timeouts.
    Uploads media once to get a Telegram file_id, then reuses it for all users.
    """
    bot = TeleBot(TOKEN, parse_mode='html')
    try:
        ann = bot_models.Announcement.objects.get(id=announcement_id)
    except bot_models.Announcement.DoesNotExist:
        return

    markup = _build_inline_markup(ann.button_text, ann.button_url)
    users = list(User.objects.all())

    delivered = 0
    photo_file_id = None
    video_file_id = None

    # If there's media, upload once to obtain file_id
    if ann.video:
        for user in users:
            try:
                with ann.video.open('rb') as f:
                    msg = bot.send_video(user.telegram_id, f, caption=ann.text or None, reply_markup=markup)
                delivered += 1
                video_file_id = msg.video.file_id if getattr(msg, 'video', None) else None
                break
            except ApiException as e:
                err = str(e.args)
                if "deactivated" in err or "blocked by the user" in err:
                    user.is_active = False
                    user.save(update_fields=["is_active"])
                continue
            except Exception:
                continue
    elif ann.photo:
        for user in users:
            try:
                with ann.photo.open('rb') as f:
                    msg = bot.send_photo(user.telegram_id, f, caption=ann.text or None, reply_markup=markup)
                delivered += 1
                if getattr(msg, 'photo', None):
                    photo_file_id = msg.photo[-1].file_id
                break
            except ApiException as e:
                err = str(e.args)
                if "deactivated" in err or "blocked by the user" in err:
                    user.is_active = False
                    user.save(update_fields=["is_active"])
                continue
            except Exception:
                continue

    # Send to remaining users using file_id when available
    for user in users:
        try:
            if video_file_id:
                bot.send_video(user.telegram_id, video_file_id, caption=ann.text or None, reply_markup=markup)
            elif photo_file_id:
                bot.send_photo(user.telegram_id, photo_file_id, caption=ann.text or None, reply_markup=markup)
            elif ann.video:
                with ann.video.open('rb') as f:
                    bot.send_video(user.telegram_id, f, caption=ann.text or None, reply_markup=markup)
            elif ann.photo:
                with ann.photo.open('rb') as f:
                    bot.send_photo(user.telegram_id, f, caption=ann.text or None, reply_markup=markup)
            else:
                bot.send_message(user.telegram_id, ann.text or ann.title, reply_markup=markup)
            delivered += 1
            sleep(0.03)
        except ApiException as e:
            error = str(e.args)
            if "deactivated" in error or "blocked by the user" in error:
                user.is_active = False
                user.save(update_fields=["is_active"])
                continue
        except Exception:
            continue

    ann.is_sent = True
    ann.sent_at = timezone.now()
    ann.save(update_fields=["is_sent", "sent_at"])


def kick_off_announcement_send(announcement_id: int):
    Thread(target=send_announcement_in_background, args=(announcement_id,), daemon=True).start()
