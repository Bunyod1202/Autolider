import os
from django.conf import settings
from telebot.types import BotCommand
from telebot import TeleBot

from bot.handlers.chosen_inline_result import initializer_chosen_inline_result_handlers
from bot.utils.constants import BASE_URL, BOT_COMMANDS

from bot.handlers.message import initializer_message_handlers
from bot.handlers.callback_query import initializer_callback_query_handlers
from bot.handlers.inline_query import initializer_inline_query_handlers
from bot.handlers.channel_post import initializer_channel_post_handlers
from bot.handlers.pre_checkout_query_handler import initializer_pre_checkout_query_handlers


def bot_initializer(token):
    bot: TeleBot = TeleBot(token, parse_mode='html')

    # Only set webhook/commands in non-debug (production) unless explicitly allowed
    allow_webhook = os.getenv("INIT_WEBHOOK")
    should_init = (not getattr(settings, 'DEBUG', False)) if allow_webhook is None else allow_webhook == "1"
    if should_init:
        try:
            bot.set_webhook(f"{BASE_URL}/bot/{token}/")
            bot.set_my_commands([BotCommand(command['command'], command['description']) for command in BOT_COMMANDS])
        except Exception as e:
            # Avoid crashing app on webhook setup issues (e.g., local dev)
            print(f"Webhook/commands init skipped: {e}")

    initializer_message_handlers(bot)
    initializer_callback_query_handlers(bot)
    initializer_inline_query_handlers(bot)
    initializer_channel_post_handlers(bot)
    initializer_pre_checkout_query_handlers(bot)
    initializer_chosen_inline_result_handlers(bot)

    return bot
