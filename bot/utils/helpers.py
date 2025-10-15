import hashlib
from time import sleep

from django.utils import timezone
from requests import post
from telebot import TeleBot, types
from telebot.apihelper import ApiException

from users.models import User
from bot.models import Constant

from bot.utils.constants import CONSTANT, BASE_URL


def is_phone_number(raw: str):
    if any([
        all([raw.startswith("+998"), raw[1:].isdigit(), len(raw) == 13]),
        all([raw.startswith("998"), raw.isdigit(), len(raw) == 12]),
        all([raw.isdigit(), len(raw) == 9])
    ]):
        return True
    return False


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
                    reply_markup=message.reply_markup,
                    protect_content=True,
                )
            elif message.voice:
                bot.send_voice(
                    user.telegram_id,
                    message.voice.file_id,
                    caption=message.html_caption,
                    reply_markup=message.reply_markup,
                    protect_content=True,
                )
            elif message.video:
                bot.send_video(
                    user.telegram_id,
                    message.video.file_id,
                    caption=message.html_caption,
                    reply_markup=message.reply_markup,
                    protect_content=True,
                )
            elif message.photo:
                bot.send_photo(
                    user.telegram_id,
                    message.photo[-1].file_id,
                    caption=message.html_caption,
                    reply_markup=message.reply_markup,
                    protect_content=True,
                )
            else:
                bot.send_message(
                    user.telegram_id,
                    message.html_text,
                    reply_markup=message.reply_markup,
                    protect_content=True,
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
        ),
        protect_content=True,
    )
