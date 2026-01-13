import traceback
from threading import Thread

from django.db.models import Q
from django.utils import timezone
from telebot import types, TeleBot

from bot.utils.constants import USER, LANGUAGE, CONSTANT
from bot.utils.helpers import extract_full_name, get_keyboard_markup, sending_post, is_phone_number, get_constant, \
    get_main_keyboard_markup, normalize_phone_number
from bot.models import Text
from payments.models import Provider, Payment
from subscriptions.models import Tariff, Subscription
from users.models import User, Log
from tests.models import Exam, ExamAccess, ExamAttempt, AttemptQuestion
from quizzes.models import Option, Quiz, Theme

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
        Log.objects.create(
                    user=user,
                    reason=USER.LOG.TYPE.GENERAL_ERROR,
                    text=f"CUSTOM: {json.dumps(user.data)}"
                )
        if user.check_step(USER.STEP.WAITING_FOR_PAYMENT):
            tariff_id, provider_id, message_id = user.data.split()
            try:
                Log.objects.create(
                    user=user,
                    reason=USER.LOG.TYPE.GENERAL_ERROR,
                    text=f"Back pressed during payment: deleting invoice message_id={message_id}"
                )
            except Exception:
                pass
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
        # Exams: entry from main via Stat test or Start exam
        exams_label = getattr(user.text, 'exams', 'Stat test')
        start_label = getattr(user.text, 'start_exam', 'Start exam')
        if user.check_step(USER.STEP.MAIN) and message.text in (exams_label, start_label):
            if not user.is_active:
                bot.send_message(message.chat.id, getattr(user.text, 'subscription_required', 'Imtihonlar faqat obuna uchun.'))
                return
            if not user.phone_number:
                user.set_step(USER.STEP.EXAM_PROMPT_PHONE)
                bot.send_message(
                    message.chat.id,
                    getattr(user.text, 'enter_phone_for_exam', 'Telefon raqamingizni kiriting'),
                    reply_markup=get_keyboard_markup([user.text.back, ])
                )
            else:
                accesses = ExamAccess.objects.filter(user=user, exam__is_active=True).select_related('exam').order_by('exam__date')
                if not accesses.exists():
                    bot.send_message(message.chat.id, getattr(user.text, 'no_exam_access', 'Sizga imtihon ruxsati berilmagan'))
                    return
                user.set_step(USER.STEP.SELECT_EXAM)
                buttons = [[f"ID{acc.exam.id} — {acc.exam.title} — {acc.exam.date.strftime('%d.%m.%Y %H:%M')}"] for acc in accesses]
                buttons.append(user.text.back)
                bot.send_message(
                    message.chat.id,
                    getattr(user.text, 'choose_exam', 'Imtihonni tanlang'),
                    reply_markup=get_keyboard_markup(buttons)
                )
            return
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
        elif user.check_step(USER.STEP.EXAM_PROMPT_PHONE):
            normalized = normalize_phone_number(message.text)
            if normalized:
                user.phone_number = normalized
                user.set_step()
                # After login, main menu will show Stat test; also offer direct exam list
                accesses = ExamAccess.objects.filter(user=user, exam__is_active=True).select_related('exam').order_by('exam__date')
                if accesses.exists():
                    user.set_step(USER.STEP.SELECT_EXAM)
                    buttons = [[f"ID{acc.exam.id} — {acc.exam.title} — {acc.exam.date.strftime('%d.%m.%Y %H:%M')}"] for acc in accesses]
                    buttons.append(user.text.back)
                    bot.send_message(
                        message.chat.id,
                        getattr(user.text, 'choose_exam', 'Imtihonni tanlang'),
                        reply_markup=get_keyboard_markup(buttons)
                    )
                else:
                    bot.send_message(message.chat.id, getattr(user.text, 'no_exam_access', 'Sizga imtihon ruxsati berilmagan'))
                    go_to_main(message, user)
            else:
                bot.send_message(
                    message.chat.id,
                    getattr(user.text, 'enter_phone_for_exam', 'Telefon raqamingizni kiriting'),
                    reply_markup=get_keyboard_markup([user.text.back, ])
                )
        elif user.check_step(USER.STEP.SELECT_EXAM):
            import re
            m = re.match(r"^ID(\d+)\b", message.text or '')
            if not m:
                accesses = ExamAccess.objects.filter(user=user, exam__is_active=True).select_related('exam').order_by('exam__date')
                if not accesses.exists():
                    bot.send_message(message.chat.id, getattr(user.text, 'no_exam_access', 'Sizga imtihon ruxsati berilmagan'))
                    go_to_main(message, user)
                    return
                buttons = [[f"ID{acc.exam.id} — {acc.exam.title} — {acc.exam.date.strftime('%d.%m.%Y %H:%M')}"] for acc in accesses]
                buttons.append(user.text.back)
                bot.send_message(
                    message.chat.id,
                    getattr(user.text, 'choose_exam', 'Imtihonni tanlang'),
                    reply_markup=get_keyboard_markup(buttons)
                )
                return
            exam_id = int(m.group(1))
            try:
                exam = Exam.objects.get(id=exam_id, is_active=True)
            except Exam.DoesNotExist:
                bot.send_message(message.chat.id, getattr(user.text, 'no_exam_access', 'Sizga imtihon ruxsati berilmagan'))
                go_to_main(message, user)
                return
            attempt = ExamAttempt.objects.filter(exam=exam, user=user, finished_at__isnull=True).first()
            if not attempt:
                if exam.type == Exam.Type.FINAL:
                    pool = list(Quiz.objects.filter(is_active=True))
                else:
                    pool = list(Quiz.objects.filter(is_active=True, theme__in=exam.topics.all()))
                if len(pool) < exam.question_count:
                    bot.send_message(message.chat.id, getattr(user.text, 'insufficient_questions', 'Savollar yetarli emas'))
                    try:
                        from bot.utils.constants import CHAT_ID_FOR_NOTIFIER
                        bot.send_message(CHAT_ID_FOR_NOTIFIER, f"Exam {exam.title}: Not enough questions ({len(pool)}/{exam.question_count})")
                    except Exception:
                        pass
                    go_to_main(message, user)
                    return
                import random
                selected = random.sample(pool, exam.question_count)
                attempt = ExamAttempt.objects.create(
                    exam=exam,
                    user=user,
                    total_questions=exam.question_count,
                )
                AttemptQuestion.objects.bulk_create([
                    AttemptQuestion(attempt=attempt, question=q, order=i + 1) for i, q in enumerate(selected)
                ])
            unanswered = attempt.attempt_questions.filter(user_answer__isnull=True).order_by('order').first()
            if not unanswered:
                bot.send_message(message.chat.id, "Ushbu imtihon yakunlangan.")
                go_to_main(message, user)
                return
            user.set_step(USER.STEP.EXAM_IN_PROGRESS, str(attempt.id))
            quiz = unanswered.question
            opts = [opt.text(user.text.language) for opt in quiz.options.all()]
            bot.send_message(
                message.chat.id,
                f"Savol {unanswered.order}/{attempt.total_questions}:\n\n{quiz.question(user.text.language)}",
                reply_markup=get_keyboard_markup([[t] for t in opts] + [user.text.back])
            )
        elif user.check_step(USER.STEP.EXAM_IN_PROGRESS):
            try:
                attempt_id = int((user.data or '').split()[0])
                attempt = ExamAttempt.objects.get(id=attempt_id, user=user)
            except Exception:
                go_to_main(message, user)
                return
            current_q = attempt.attempt_questions.filter(user_answer__isnull=True).order_by('order').first()
            if not current_q:
                go_to_main(message, user)
                return
            chosen = None
            for opt in current_q.question.options.all():
                if opt.text(user.text.language) == message.text:
                    chosen = opt
                    break
            if chosen is None:
                opts = [opt.text(user.text.language) for opt in current_q.question.options.all()]
                bot.send_message(
                    message.chat.id,
                    f"Savol {current_q.order}/{attempt.total_questions}:\n\n{current_q.question.question(user.text.language)}",
                    reply_markup=get_keyboard_markup([[t] for t in opts] + [user.text.back])
                )
                return
            current_q.user_answer = chosen
            current_q.is_correct = bool(chosen.is_correct)
            current_q.save(update_fields=['user_answer', 'is_correct'])
            next_q = attempt.attempt_questions.filter(user_answer__isnull=True).order_by('order').first()
            if next_q:
                opts = [opt.text(user.text.language) for opt in next_q.question.options.all()]
                bot.send_message(
                    message.chat.id,
                    f"Savol {next_q.order}/{attempt.total_questions}:\n\n{next_q.question.question(user.text.language)}",
                    reply_markup=get_keyboard_markup([[t] for t in opts] + [user.text.back])
                )
                return
            from django.utils import timezone as _tz
            attempt.correct_count = attempt.attempt_questions.filter(is_correct=True).count()
            attempt.wrong_count = attempt.total_questions - attempt.correct_count
            attempt.finished_at = _tz.now()
            attempt.spent_time = int((attempt.finished_at - attempt.started_at).total_seconds())
            attempt.save(update_fields=['correct_count', 'wrong_count', 'finished_at', 'spent_time'])
            user.set_step()
            bot.send_message(
                message.chat.id,
                f"Natija:\nTo'g'ri: {attempt.correct_count}\nNoto'g'ri: {attempt.wrong_count}\nJami: {attempt.total_questions}\nVaqt: {attempt.spent_time} sekund",
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
                try:
                    Log.objects.create(
                        user=user,
                        reason=USER.LOG.TYPE.GENERAL_ERROR,
                        text=(
                            f"Preparing invoice: tariff_id={tariff.id} days={tariff.days} "
                            f"price={tariff.price} provider_id={provider.id} "
                            f"provider_token_present={'yes' if bool(provider.data) else 'no'} {provider.data}"
                        ),
                    )
                except Exception:
                    pass
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
                    'UZS',
                    [
                        types.LabeledPrice(
                            tariff.name(user.text.language),
                            tariff.price * 100,
                        ),
                    ],
                    protect_content=True,
                )
                user.set_step(USER.STEP.WAITING_FOR_PAYMENT, f"{tariff.id} {provider.id} {msg.message_id}")
                try:
                    Log.objects.create(
                        user=user,
                        reason=USER.LOG.TYPE.GENERAL_ERROR,
                        text=(
                            f"Invoice sent: message_id={msg.message_id} payload='{tariff.id} {provider.id}' "
                            f"amount={tariff.price} currency=UZS "
                            f"tariff='{tariff.name(user.text.language)}' provider='{provider.name(user.text.language)}'"
                        ),
                    )
                except Exception:
                    pass
            except Provider.DoesNotExist:
                try:
                    Log.objects.create(
                        user=user,
                        reason=USER.LOG.TYPE.GENERAL_ERROR,
                        text=f"Provider not found for input='{message.text}'"
                    )
                except Exception:
                    pass
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
        try:
            # Log payment received
            Log.objects.create(
                user=user,
                reason=USER.LOG.TYPE.PAYMENT_RECEIVED,
                text=f"Payment received: {message}"
            )
            
            # Log invoice payload
            Log.objects.create(
                user=user,
                reason=USER.LOG.TYPE.PAYMENT_INFO,
                text=f"Invoice payload: {message.successful_payment.invoice_payload}"
            )
            
            tariff_id, provider_id = message.successful_payment.invoice_payload.split()
            Log.objects.create(
                user=user,
                reason=USER.LOG.TYPE.PAYMENT_INFO,
                text=f"Parsed payload - tariff_id: {tariff_id}, provider_id: {provider_id}"
            )
            
            tariff: Tariff = Tariff.objects.get(id=tariff_id)
            provider: Provider = Provider.objects.get(id=provider_id)
            
            Log.objects.create(
                user=user,
                reason=USER.LOG.TYPE.PAYMENT_INFO,
                text=f"Found tariff: {tariff.name(user.text.language)}, provider: {provider.name(user.text.language)}"
            )
            Log.objects.create(
                user=user,
                reason=USER.LOG.TYPE.PAYMENT_INFO,
                text=(
                    f"Starting payment processing - "
                    f"charge_id: {message.successful_payment.provider_payment_charge_id}, "
                    f"amount: {message.successful_payment.total_amount}"
                ),
            )
            
            # Get or create subscription
            last_subscription = user.subscriptions.filter(is_checked=False, expire_time__lt=now).first()
            expire_time = now + timedelta(days=tariff.duration_days)
            
            Log.objects.create(
                user=user,
                reason=USER.LOG.TYPE.PAYMENT_INFO,
                text=f"Creating subscription - tariff: {tariff.name(user.text.language)}, expires: {expire_time}"
            )
            
            # Create subscription
            subscription = Subscription.objects.create(
                user=user,
                tariff=tariff,
                expire_time=expire_time,
            )
            
            Log.objects.create(
                user=user,
                reason=USER.LOG.TYPE.PAYMENT_INFO,
                text=f"Creating payment record - provider: {provider.name(user.text.language)}"
            )
            
            # Create payment record
            payment = Payment.objects.create(
                user=user,
                provider=provider,
                subscription=subscription,
                provider_transaction_id=message.successful_payment.provider_payment_charge_id,
                amount=tariff.price,
            )
            
            Log.objects.create(
                user=user,
                reason=USER.LOG.TYPE.PAYMENT_SUCCESS,
                text=(
                    f"Payment processed successfully - "
                    f"payment_id: {payment.id}, "
                    f"subscription_id: {subscription.id}"
                )
            )
            
            # Send success message to user
            bot.send_message(
                message.chat.id,
                user.text.successful_payment_info.format(
                    expire_time=expire_time.strftime("%d.%m.%Y"),
                ),
                reply_markup=reply_keyboard_remove,
            )
            
            Log.objects.create(
                user=user,
                reason=USER.LOG.TYPE.PAYMENT_INFO,
                text="Success message sent to user"
            )
            
        except Exception as e:
            # Log any errors that occur during payment processing
            Log.objects.create(
                user=user,
                reason=USER.LOG.TYPE.PAYMENT_ERROR,
                text=f"Error processing payment: {str(e)}",
            )
            
            # Log the full traceback for debugging
            import traceback
            Log.objects.create(
                user=user,
                reason=USER.LOG.TYPE.PAYMENT_ERROR,
                text=f"Payment error traceback: {traceback.format_exc()}",
            )
            
            # Notify user about the error
            try:
                bot.send_message(
                    message.chat.id,
                    user.text.payment_error_message or "Kechirasiz, to'lovni qayta ishlashda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring yoki administratorga murojaat qiling.",
                )
            except Exception as send_error:
                Log.objects.create(
                    user=user,
                    reason=USER.LOG.TYPE.PAYMENT_ERROR,
                    text=f"Failed to send error message to user: {str(send_error)}"
                )
                
            # Re-raise the exception to ensure it's not silently caught
            raise
            pass
        # Extend from the latest unchecked subscription's expire_time if it is in the future,
        # otherwise start from now. This accumulates remaining days properly.
        last_unchecked = user.subscriptions.filter(is_checked=False).order_by('-expire_time').first()
        base_time = now
        if last_unchecked and last_unchecked.expire_time > now:
            base_time = last_unchecked.expire_time
        expire_time = base_time + timezone.timedelta(days=tariff.days)
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])  # persist activation
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
        try:
            Log.objects.create(
                user=user,
                reason=USER.LOG.TYPE.GENERAL_ERROR,
                text=(
                    f"Subscription updated: subscription_id={subscription.id} expire_time={expire_time.strftime('%Y-%m-%d')}"
                )
            )
        except Exception:
            pass
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
