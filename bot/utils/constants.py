TOKEN = "7201071278:AAGG3FP-GQGMPgTIAbJmSpwgXga-Ak0pAa0"

BASE_URL = "https://avtolider.medias.uz"


CHAT_ID_FOR_NOTIFIER = -1002498547077


class LANGUAGE:
    UZ = '0'
    RU = '1'

    DICT = {
        UZ: "🇺🇿 O'zbekcha",
        RU: "🇷🇺 Русский",
    }

    REVERSE = {
        "🇺🇿 O'zbekcha": UZ,
        "🇷🇺 Русский": RU,
    }

    CHOICE = DICT.items()


class USER:

    class STEP:

        MAIN = '0'
        SELECT_LANGUAGE = '1'
        GETTING_FULL_NAME = '2'
        GETTING_PHONE_NUMBER = '3'

        SELECT_TARIFF = '4'
        SELECT_PROVIDER = '41'
        WAITING_FOR_PAYMENT = '42'

        GETTING_COMMENT = '5'

        GETTING_POST_MESSAGE = '100'

        DICT = {
            MAIN: "Main",
            SELECT_LANGUAGE: "Select language",
            GETTING_FULL_NAME: "Getting full name",
            GETTING_PHONE_NUMBER: "Getting phone number",
            GETTING_POST_MESSAGE: "Getting post message",
        }

        CHOICES = list(DICT.items())

    class CALLBACK:
        pass

    class LOG:

        class TYPE:
            GENERAL_ERROR = '0'
            API_EXCEPTION_ON_CALLBACK_QUERY_HANDLER = '1'
            EXCEPTION_ON_CALLBACK_QUERY_HANDLER = '2'

            DICT = {
                GENERAL_ERROR: "General error",
                API_EXCEPTION_ON_CALLBACK_QUERY_HANDLER: "API exception on callback query handler",
                EXCEPTION_ON_CALLBACK_QUERY_HANDLER: "Exception on callback query handler",
            }

            CHOICES = list(DICT.items())


class CONSTANT:
    MAIN_PHOTO_URL = '1'
    COMMENTS_CHANNEL_ID = '2'

    DEFAULT = {
        MAIN_PHOTO_URL: "https://telegra.ph/file/2d8d164ee4492e36da3aa.jpg",
        COMMENTS_CHANNEL_ID: "-1002447363829"
    }

    DICT = {
        MAIN_PHOTO_URL: "Main photo url",
        COMMENTS_CHANNEL_ID: "Comments channel id",
    }

    CHOICES = DICT.items()


class MESSAGE:

    class TYPE:
        TEXT = '0'
        PHOTO = '1'
        AUDIO = '2'
        VOICE = '3'
        VIDEO = '4'

        DICT = {
            TEXT: "Matnli xabar",
            PHOTO: "Fotosuratli xabar",
            AUDIO: "Audio xabar",
            VOICE: "Ovozli xabar",
            VIDEO: "Video xabar"
        }

        CHOICES = DICT.items()


BOT_COMMANDS = [
    {
        "command": 'start',
        "description": "Foydalanishni boshlash"
    }
]
