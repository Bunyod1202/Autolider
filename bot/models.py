from django.db import models
from bot.utils.constants import CONSTANT, LANGUAGE


class Text(models.Model):
    language = models.CharField(
        max_length=3,
        default=LANGUAGE.UZ,
        choices=LANGUAGE.CHOICE,
        unique=True,
    )
    welcome_text = models.TextField(
        default="Assalom aleykum, welcome text..."
    )
    help_info = models.TextField(
        default="Bu xabarda botdan foydalanish bo'yicha ma'lumotlar bo'lishi kerak"
    )
    main_text = models.TextField(
        default="<b>@SaveMeRobot</b> sizning yordamchingiz 😊"
    )
    you_are_banned = models.TextField(
        default="Siz moderatorlar tomonidan block holatiga tushirilgansiz, qo'shimcha ma'lumot uchun bizga murojaat qiling."
    )
    message_too_old = models.TextField(
        default="Ushbu xabar juda eski, /start buyrug'i bilan qaytadan boshlang."
    )
    send_me_post_message = models.TextField(
        default=(
            "Foydalanuvchilarga yubormoqchi bo'lgan xabaringizni menga yuboring.\n\n"
            "<b>Diqqat: foydalanuvchilarga oddiy textli, fotosuratli (faqat bitta), videoli, ovozli yoki audioli xabar yuborishingiz mumkin.</b>\n\n"
            "<i>Xabar yuborish boshlanganidan so'ng uni to'xtatish imkonsiz, shu sababli yuborayotgan xabaringiz to'g'riligiga ishonch hosil qiling.</i>"
        )
    )
    posting_starts_please_wait = models.TextField(
        default="⏳ Xabar yuborish jarayoni boshlandi, iltimos kutib turing, yakunda xabar beraman."
    )
    posting_end = models.TextField(
        default=(
            "✅ Xabar foydalanuvchilarga yuborildi.\n\nBarcha foydalanuvchilar: {user_counts} ta\n"
            "Xabar yuborilgan foydalanuvchilar: {total} ta"
        )
    )
    getting_full_name_info = models.TextField(
        default="Ism familyangizni kiriting.",
    )
    getting_phone_number_info = models.TextField(
        default="Telefon raqamingizni yuboring.",
    )
    selecting_tariff_for_prolonging_the_subscription = models.TextField(
        default=(
            "Sizning obunangiz: {expire_date} gacha amal qiladi\n\n"
            "Uzaytirmoqchi bo'lsangiz quyidagi tariflardan birini tanlang:"
        ),
    )
    selecting_tariff_for_subscription = models.TextField(
        default=(
            "Hozircha obunangiz aktiv holatda emas.\n\n"
            "Obunangizni aktivlashtirish uchun quyidagi tariflardan birini tanlang:"
        ),
    )
    selecting_provider_for_subscription = models.TextField(
        default="To'lov usulini tanlang:",
    )
    invoice_title = models.TextField(
        max_length=32,
        default="{tariff_name} uchun to'lov",
    )
    invoice_description = models.TextField(
        max_length=255,
        default="{tariff_name} uchun {price:,} so'm to'lovni {provider_name} orqali to'lash uchun hisob.",
    )
    successful_payment_info = models.TextField(
        default="✅ Tabriklaymiz! Sizning obunangiz {expire_time} gacha aktiv.",
    )
    your_subscription_is_expired = models.TextField(
        default="Sizning obunangiz muddati tugadi, obunani uzaytirib olishni unutmang."
    )
    getting_comment_info = models.TextField(
        default="Bot haqida o'z fikrlaringizni qoldirishingiz mumkin.",
    )
    comments_sent = models.TextField(
        default="✅ Xabar yuborildi, e'tiboringiz uchun rahmat.",
    )

    themes = models.CharField(
        max_length=127,
        default="Mavzular",
    )
    total_quizzes_count = models.CharField(
        max_length=127,
        default="Jami savollar soni:",
    )
    start_testing = models.CharField(
        max_length=127,
        default="Testni boshlash",
    )
    tests_not_found = models.CharField(
        max_length=127,
        default="Siz hozircha birorta ham test ishlamagansiz.",
    )
    you_are_not_active = models.CharField(
        max_length=255,
        default=(
            "❌ Uzr. Ushbu bo'lim faqat aktiv obunachilar uchun mavjud. "
            "Iltimos obunani aktivlashtirib, so'ngra qayta urinib ko'ring."
        ),
    )
    test_result = models.CharField(
        max_length=127,
        default="test natijalari",
    )
    see_more = models.CharField(
        max_length=127,
        default="To'liq ko'rish",
    )
    theme = models.CharField(
        max_length=127,
        default="💡Mavzu:",
    )
    spent_time = models.CharField(
        max_length=127,
        default="⏰Ketgan vaqt:",
    )
    correct_answers = models.CharField(
        max_length=127,
        default="🔑 To'g'ri javob berilgan:",
    )
    correct_answers_info = models.CharField(
        max_length=127,
        default="{correct_answers_count}/{quizzes_count} savolga ({percentage}%)",
    )

    left_hours = models.CharField(
        max_length=31,
        default="{hours} soat",
    )
    left_minutes = models.CharField(
        max_length=31,
        default="{minutes} minut",
    )
    left_seconds = models.CharField(
        max_length=31,
        default="{seconds} sekund",
    )
    left = models.CharField(
        max_length=31,
        default="ketdi",
    )

    requesting_phone_number = models.CharField(
        max_length=63,
        default="📞 Telefon raqamni yuborish",
    )
    tests = models.CharField(
        max_length=63,
        default="🖋 Mavzulashtirilgan test ishlash",
    )
    subscription = models.CharField(
        max_length=63,
        default="🗓 Obunani aktivlashtirish",
    )
    comment = models.CharField(
        max_length=63,
        default="✍️ Fikr qoldirish",
    )
    help = models.CharField(
        max_length=63,
        default="🆘 Yordam",
    )
    change_language = models.CharField(
        max_length=63,
        default="🔄 Tilni almashtirish",
    )
    back = models.CharField(
        max_length=63,
        default="🔙Ortga"
    )
    # Modal/back flow texts for test page
    are_you_sure = models.CharField(
        max_length=255,
        default="Chiqmoqchimisiz? Saqlab, keyin davom ettirishingiz mumkin.",
    )
    exit_label = models.CharField(
        max_length=63,
        default="Chiqish",
    )
    continue_label = models.CharField(
        max_length=63,
        default="Davom etish",
    )
    added_time = models.DateTimeField(
        auto_now_add=True,
    )
    last_updated_time = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return LANGUAGE.DICT.get(self.language)


class Constant(models.Model):
    key = models.CharField(
        max_length=15,
        choices=CONSTANT.CHOICES,
        unique=True
    )
    data = models.TextField()
    added_time = models.DateTimeField(
        auto_now_add=True,
    )
    last_updated_time = models.DateTimeField(
        auto_now=True,
    )

    @property
    def actual_data(self):
        if self.data.isdigit():
            return int(self.data)
        return self.data

    def __str__(self):
        return f"{self.key}: {self.data}"


class Announcement(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='announcements/', blank=True, null=True)
    video = models.FileField(upload_to='announcements/', blank=True, null=True)
    button_text = models.CharField(max_length=127, blank=True, null=True)
    button_url = models.URLField(blank=True, null=True)

    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(blank=True, null=True)
    added_time = models.DateTimeField(auto_now_add=True)
    last_updated_time = models.DateTimeField(auto_now=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.photo and self.video:
            raise ValidationError("Rasm va video bir vaqtning o'zida yuklanmasin. Faqat bittasini tanlang.")

    def __str__(self):
        return f"{self.title}"

