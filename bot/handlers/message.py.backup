import traceback
from threading import Thread

from django.db.models import Q
from django.utils import timezone
from telebot import types, TeleBot

from bot.utils.constants import USER, LANGUAGE, CONSTANT
from bot.utils.helpers import extract_full_name, get_keyboard_markup, sending_post, is_phone_number, get_constant, \
    get_main_keyboard_markup
from bot.models import Text
from payments.models import Provider, Payment
from subscriptions.models import Tariff, Subscription
from users.models import User, Log

reply_keyboard_remove = types.ReplyKeyboardRemove()


def initializer_message_handlers(_: TeleBot):
    def auth(handler, bot: TeleBot = _):
        def wrapper(message: types.Message, bot: TeleBot = bot):
            try:
                user: User = User.objects.get(telegram_id=message.from_user.id)
                try:
                    handler(message, user)
                except Exception as e:
                    Log.objects.create(
                        user=user,
                        reason=USER.LOG.TYPE.GENERAL_ERROR,
                        text=traceback.print_exc() or e.args or "No error message"
                    )
            except User.DoesNotExist:
                start_handler(message)

        return wrapper

    def go_to_main(message: types.Message, user: User, bot: TeleBot = _):
        user.set_step()
        bot.send_photo(
            message.chat.id,
            get_constant(CONSTANT.MAIN_PHOTO_URL),
            user.text.main_text,
            reply_markup=get_main_keyboard_markup(user)
        )

    @_.message_handler(commands=['start'])
    def start_handler(message: types.Message, bot: TeleBot = _):
        try:
            user: User = User.objects.get(telegram_id=message.from_user.id)
            if user.text:
                go_to_main(message, user)
                return
            change_language_handler(message, user)
        except User.DoesNotExist:
            full_name = extract_full_name(message)
            User.objects.create(
                telegram_id=message.from_user.id,
                full_name=full_name,
                username=message.from_user.username,
                step=USER.STEP.SELECT_LANGUAGE
            )
            bot.send_message(
                message.chat.id,
                "Kerakli tilni tanlang\n\nВыберите желаемый язык",
                reply_markup=get_keyboard_markup([
                    str(text) for text in Text.objects.all()
                ])
            )

    @_.message_handler(commands=['subscription'])
    @_.message_handler(regexp="^🗓 ")
    @auth
    def subscription_handler(message: types.Message, user: User, bot: TeleBot = _):
        if user.check_step(USER.STEP.MAIN):
            user.set_step(USER.STEP.SELECT_TARIFF)
            subscription = user.subscriptions.filter(is_checked=False).last()
            reply_markup = get_keyboard_markup([
                    *[
                        tariff.name(user.text.language) for tariff in Tariff.objects.filter(is_active=True)
                    ],
                    user.text.back
                ]
            )
            if subscription:
                bot.send_message(
                    message.chat.id,
                    user.text.selecting_tariff_for_prolonging_the_subscription.format(
                        expire_date=subscription.expire_time.strftime('%d.%m.%Y'),
                    ),
                    reply_markup=reply_markup,
                )
            else:
                bot.send_message(
                    message.chat.id,
                    user.text.selecting_tariff_for_subscription,
                    reply_markup=reply_markup,
                )

    @_.message_handler(commands=['comments'])
    @_.message_handler(regexp="^✍️ ")
    @auth
    def comments_handler(message: types.Message, user: User, bot: TeleBot = _):
        if user.check_step(USER.STEP.MAIN):
            user.set_step(USER.STEP.GETTING_COMMENT)
            bot.send_message(
                message.chat.id,
                user.text.getting_comment_info,
                reply_markup=get_keyboard_markup([user.text.back, ])
            )

    @_.message_handler(commands=['language'])
    @_.message_handler(regexp="^🔄 ")
    @auth
    def change_language_handler(message: types.Message, user: User, bot: TeleBot = _):
        if user.check_step(USER.STEP.MAIN):
            user.set_step(USER.STEP.SELECT_LANGUAGE)
            bot.send_message(
                message.chat.id,
                "Kerakli tilni tanlang\n\nВыберите желаемый язык",
                reply_markup=get_keyboard_markup([
                    str(text) for text in Text.objects.all()
                ])
            )

    @_.message_handler(commands=['post'])
    @auth
    def post_handler(message: types.Message, user: User, bot: TeleBot = _):
        if user.is_admin:
            user.set_step(USER.STEP.GETTING_POST_MESSAGE)
            bot.reply_to(
                message,
                user.text.send_me_post_message,
                reply_markup=get_keyboard_markup([user.text.back])
            )

    @_.message_handler(regexp="^🔙 ")
    @auth
    def back_handler(message: types.Message, user: User, bot: TeleBot = _):
        if user.check_step(USER.STEP.WAITING_FOR_PAYMENT):
            tariff_id, provider_id, message_id = user.data.split()
            bot.delete_message(
                message.chat.id,
                message_id,
            )
            user.set_step(USER.STEP.SELECT_PROVIDER, tariff_id)
            bot.send_message(
                message.chat.id,
                user.text.selecting_provider_for_subscription,
                reply_markup=get_keyboard_markup([
                    [
                        provider.name(user.text.language) for provider in Provider.objects.filter(is_active=True)
                    ],
                    user.text.back,
                ])
            )
        elif user.check_step(USER.STEP.SELECT_PROVIDER):
            user.set_step()
            subscription_handler(message, user)
        else:
            go_to_main(message, user)

    @_.message_handler(func=lambda message: True)
    @auth
    def all_message_handler(message: types.Message, user: User, bot: TeleBot = _):
        if user.check_step(USER.STEP.GETTING_POST_MESSAGE) and user.is_admin:
            user.set_step()
            bot.reply_to(
                message,
                user.text.posting_starts_please_wait,
            )
            thread = Thread(target=sending_post, args=(bot, message, user))
            thread.start()
        elif user.check_step(USER.STEP.SELECT_LANGUAGE):
            try:
                text = Text.objects.get(language=LANGUAGE.REVERSE.get(message.text))
                user.text = text
                if user.phone_number:
                    go_to_main(message, user)
                else:
                    user.set_step(USER.STEP.GETTING_FULL_NAME)
                    bot.send_message(
                        message.chat.id,
                        user.text.getting_full_name_info,
                        reply_markup=reply_keyboard_remove
                    )
            except Text.DoesNotExist:
                bot.send_message(
                    message.chat.id,
                    "Kerakli tilni tanlang\n\nВыберите желаемый язык",
                    reply_markup=get_keyboard_markup([
                        str(text) for text in Text.objects.all()
                    ])
                )
        elif user.check_step(USER.STEP.GETTING_FULL_NAME):
            user.full_name = message.text.replace('<', '').replace('>', '')
            user.set_step(USER.STEP.GETTING_PHONE_NUMBER)
            bot.send_message(
                message.chat.id,
                user.text.getting_phone_number_info,
                reply_markup=get_keyboard_markup([user.text.requesting_phone_number])
            )
        elif user.check_step(USER.STEP.GETTING_PHONE_NUMBER):
            if is_phone_number(message.text):
                user.phone_number = message.text
                bot.send_message(
                    message.chat.id,
                    user.text.welcome_text,
                    reply_markup=reply_keyboard_remove,
                )
                go_to_main(message, user)
            else:
                bot.send_message(
                    message.chat.id,
                    user.text.getting_phone_number_info,
                    reply_markup=get_keyboard_markup([user.text.requesting_phone_number])
                )
        elif user.check_step(USER.STEP.GETTING_COMMENT):
            bot.send_message(
                get_constant(CONSTANT.COMMENTS_CHANNEL_ID),
                f"<a href='tg://user?id={message.chat.id}'>{user.full_name}</a>[{user.phone_number}]: {message.html_text}",
            )
            bot.send_message(
                message.chat.id,
                user.text.comments_sent,
                reply_markup=reply_keyboard_remove,
            )
            go_to_main(message, user)
        elif user.check_step(USER.STEP.SELECT_TARIFF):
            try:
                tariff: Tariff = Tariff.objects.get(Q(name_uz=message.text) | Q(name_ru=message.text))
                user.set_step(USER.STEP.SELECT_PROVIDER, tariff.id)
                bot.send_message(
                    message.chat.id,
                    user.text.selecting_provider_for_subscription,
                    reply_markup=get_keyboard_markup([
                        [
                            provider.name(user.text.language) for provider in Provider.objects.filter(is_active=True)
                        ],
                        user.text.back
                    ])
                )
            except Tariff.DoesNotExist:
                user.set_step()
                subscription_handler(message, user)
        elif user.check_step(USER.STEP.SELECT_PROVIDER):
            try:
                tariff: Tariff = Tariff.objects.get(id=user.data)
                provider: Provider = Provider.objects.get(Q(name_uz=message.text) | Q(name_ru=message.text))
                bot.send_message(
                    message.chat.id,
                    "👇",
                    reply_markup=get_keyboard_markup([user.text.back, ])
                )
                msg = bot.send_invoice(
                    message.chat.id,
                    user.text.invoice_title.format(
                        tariff_name=tariff.name(user.text.language),
                    ),
                    user.text.invoice_description.format(
                        tariff_name=tariff.name(user.text.language),
                        price=tariff.price,
                        provider_name=provider.name(user.text.language),
                    ),
                    f"{tariff.id} {provider.id}",
                    provider.data,
                    'uzs',
                    [
                        types.LabeledPrice(
                            tariff.name(user.text.language),
                            tariff.price * 100,
                        ),
                    ],
                    protect_content=True,
                )
                user.set_step(USER.STEP.WAITING_FOR_PAYMENT, f"{tariff.id} {provider.id} {msg.message_id}")
            except Provider.DoesNotExist:
                bot.send_message(
                    message.chat.id,
                    user.text.selecting_provider_for_subscription,
                    reply_markup=get_keyboard_markup([
                        *[
                            provider.name(user.text.language) for provider in Provider.objects.filter(is_active=True)
                        ]
                    ])
                )
        else:
            go_to_main(message, user)

    @_.message_handler(content_types=['successful_payment'])
    @auth
    def successful_payment_handler(message: types.Message, user: User, bot: TeleBot = _):
        now = timezone.now()
        tariff_id, provider_id = message.successful_payment.invoice_payload.split()
        tariff: Tariff = Tariff.objects.get(id=tariff_id)
        provider: Provider = Provider.objects.get(id=provider_id)
        last_subscription: Subscription = user.subscriptions.filter(is_checked=False, expire_time__lt=now)
        expire_time = now + timezone.timedelta(days=tariff.days)
        if last_subscription:
            expire_time = last_subscription.expire_time + timezone.timedelta(days=tariff.days)
        if not user.is_active:
            user.is_active = True
        subscription: Subscription = Subscription.objects.create(
            user=user,
            tariff=tariff,
            expire_time=expire_time,
        )
        Payment.objects.create(
            user=user,
            provider=provider,
            subscription=subscription,
            provider_transaction_id=message.successful_payment.provider_payment_charge_id,
            amount=tariff.price,
        )
        bot.send_message(
            message.chat.id,
            user.text.successful_payment_info.format(
                expire_time=expire_time.strftime("%d.%m.%Y"),
            ),
            reply_markup=reply_keyboard_remove,
        )
        go_to_main(message, user)

    @_.message_handler(content_types=['contact'])
    @auth
    def contact_handler(message: types.Message, user: User, bot: TeleBot = _):
        if user.check_step(USER.STEP.GETTING_PHONE_NUMBER):
            user.phone_number = message.contact.phone_number
            bot.send_message(
                message.chat.id,
                user.text.welcome_text,
                reply_markup=reply_keyboard_remove,
            )
            go_to_main(message, user)

    @_.message_handler(content_types=['audio'])
    @auth
    def voice_handler(message: types.Message, user: User, bot: TeleBot = _):
        if user.is_admin:
            if user.check_step(USER.STEP.GETTING_POST_MESSAGE):
                user.set_step()
                bot.reply_to(
                    message,
                    user.text.posting_starts_please_wait,
                )
                thread = Thread(target=sending_post, args=(bot, message, user))
                thread.start()
            else:
                bot.reply_to(
                    message,
                    f"<code>{message.audio.file_id}</code>"
                )

    @_.message_handler(content_types=['voice'])
    @auth
    def voice_handler(message: types.Message, user: User, bot: TeleBot = _):
        if user.is_admin:
            if user.check_step(USER.STEP.GETTING_POST_MESSAGE):
                user.set_step()
                bot.reply_to(
                    message,
                    user.text.posting_starts_please_wait,
                )
                thread = Thread(target=sending_post, args=(bot, message, user))
                thread.start()
            else:
                bot.reply_to(
                    message,
                    f"<code>{message.voice.file_id}</code>"
                )

    @_.message_handler(content_types=['video'])
    @auth
    def video_handler(message: types.Message, user: User, bot: TeleBot = _):
        if user.is_admin:
            if user.check_step(USER.STEP.GETTING_POST_MESSAGE):
                user.set_step()
                bot.reply_to(
                    message,
                    user.text.posting_starts_please_wait,
                )
                thread = Thread(target=sending_post, args=(bot, message, user))
                thread.start()
            else:
                bot.reply_to(
                    message,
                    f"<code>{message.video.file_id}</code>"
                )

    @_.message_handler(content_types=['photo'])
    @auth
    def photo_handler(message: types.Message, user: User, bot: TeleBot = _):
        if user.is_admin:
            if user.check_step(USER.STEP.GETTING_POST_MESSAGE):
                user.set_step()
                bot.reply_to(
                    message,
                    user.text.posting_starts_please_wait,
                )
                thread = Thread(target=sending_post, args=(bot, message, user))
                thread.start()
            else:
                bot.reply_to(
                    message,
                    f"<code>{message.photo[-1].file_id}</code>"
                )
