import traceback
from telebot import types, TeleBot
from telebot.apihelper import ApiException

from users.models import User, Log

from bot.utils.constants import USER


def initializer_callback_query_handlers(_: TeleBot):
    @_.callback_query_handler(func=lambda query: True)
    def callback_query_handler(query: types.CallbackQuery, bot=_):

        def _(user: User, query: types.CallbackQuery, message: types.Message, *args):
            pass

        try:
            user: User = User.objects.get(telegram_id=query.from_user.id)
            if query.data:
                step, *data = map(int, query.data.split())
                try:
                    {}[step](user, query, query.message, *data)
                    bot.answer_callback_query(query.id)
                except ApiException as e:
                    Log.objects.create(
                        user=user,
                        reason=USER.LOG.TYPE.API_EXCEPTION_ON_CALLBACK_QUERY_HANDLER,
                        text=traceback.print_exc() or e.args or "No error message"
                    )
                    bot.answer_callback_query(query.id)
                except Exception as e:
                    Log.objects.create(
                        user=user,
                        reason=USER.LOG.TYPE.EXCEPTION_ON_CALLBACK_QUERY_HANDLER,
                        text=traceback.print_exc() or e.args or "No error message"
                    )
                    bot.answer_callback_query(query.id)
        except User.DoesNotExist:
            pass
