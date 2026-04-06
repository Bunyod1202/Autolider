from telebot import TeleBot
from users.models import User, Log
from bot.utils.constants import USER


def initializer_pre_checkout_query_handlers(_: TeleBot):
    @_.pre_checkout_query_handler(func=lambda query: True)
    def checkout(pre_checkout_query, bot=_):
        # Validate invoice_payload exists
        if not pre_checkout_query.invoice_payload:
            try:
                user = User.objects.get(telegram_id=pre_checkout_query.from_user.id)
                Log.objects.create(
                    user=user,
                    reason=USER.LOG.TYPE.GENERAL_ERROR,
                    text="PreCheckout error: invoice_payload is missing"
                )
            except Exception:
                pass
            # Reject the pre-checkout query if payload is missing
            bot.answer_pre_checkout_query(
                pre_checkout_query.id,
                False,
                error_message="To'lov ma'lumotlarida xatolik. Iltimos, qayta urinib ko'ring."
            )
            return
        
        # Log incoming pre-checkout details for diagnostics
        try:
            user = User.objects.get(telegram_id=pre_checkout_query.from_user.id)
            Log.objects.create(
                user=user,
                reason=USER.LOG.TYPE.GENERAL_ERROR,
                text=(
                    f"PreCheckout received: payload={pre_checkout_query.invoice_payload} "
                    f"total_amount={pre_checkout_query.total_amount} "
                    f"currency={pre_checkout_query.currency}"
                )
            )
        except Exception:
            user = None
        # Answer pre-checkout; log success/failure
        try:
            bot.answer_pre_checkout_query(
                pre_checkout_query.id,
                True
            )
            if user:
                Log.objects.create(
                    user=user,
                    reason=USER.LOG.TYPE.GENERAL_ERROR,
                    text="PreCheckout answered: ok=True"
                )
        except Exception as e:
            if user:
                Log.objects.create(
                    user=user,
                    reason=USER.LOG.TYPE.GENERAL_ERROR,
                    text=f"PreCheckout answer failed: {e}"
                )
            raise
