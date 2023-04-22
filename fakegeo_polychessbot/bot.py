import logging
from sqlite3 import OperationalError
from croniter.croniter import CroniterBadCronError, CroniterNotAlphaError

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telethon.errors import AuthKeyUnregisteredError, FloodWaitError

from handlerusers import HandlerUsers
from session_name import SessionName
from type import Api, UserInfo
from user import User
import cronaction


class Bot:
    logger: logging.Logger
    _api: Api
    _app: Application
    _users: HandlerUsers
    _path_db: str

    def __init__(self, api: Api, token: str, path_db: str, name_db: str):
        self.logger = logging.getLogger(__name__)
        self._app = Application.builder().token(token).build()
        self._api = api
        self._path_db = path_db
        self._users = HandlerUsers(path_db, name_db)
        self._users.restore()

    async def _start(self, update: Update, _: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            """
Hi comrade.\n
How to enable this future? Follow the steps:
1) Press /auth {YOUR PHONE NUMBER}
(for ex: /auth +79992132533)
2) Then you need put /code {CODE}
(fox ex: 28204, need put 2.8.2.0.4)
3) if the schedule has changed, u can change the recurrence of sending messages
/schedule {CRON LANG} (for ex: /schedule 30 18 * * 5)
It's little hard, site can help you: https://cron.help/
More info: https://github.com/michael2to3/fakegeo-polychessbot
"""
        )

    async def _help(self, update: Update, _: ContextTypes.DEFAULT_TYPE):
        message = """
/start - Start bot
/help - Show this message
/auth PHONE_NUMBER - Replace PHONE_NUMBER to your phone for auth in tg
    ex: /auth +79992132533
/code CODE - Replace CODE to your code after make auth
    ex: /code 28204
/schedule CRON - Replace CRON to your schedule to make repeat for your schedule
    ex: /schedule 30 18 * * 5
/send - Send now your fake geolocation
    ex: /send
/delete - Delete your token and all data about you
    ex: /delete
Service for help cron: https://cron.help/#30_18_*_*_5
More info: https://github.com/michael2to3/fakegeo-polychessbot
Support: https://t.me/+EGnT6v3APokxMGYy
"""
        await update.message.reply_text(message)

    async def _auth(self, update: Update, _: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id

        if self._users.check_exist(chat_id):
            emess = "You already auth, if you want reauth you can /delete self"
            await update.message.reply_text(emess)
            return

        username = update.message.from_user.full_name
        sid = str(chat_id)
        session_name = self._path_db + SessionName().get_session_name_base(sid)

        text = update.message.text

        emess = """
Send me auth code each char separated by a dot
For example: Login code: 61516
You put: /code 6.1.5.1.6
It's need to bypass protect telegram
"""

        schedule = "30 18 * * 6"
        info = UserInfo(session_name, username, chat_id, "", -1, schedule, "")
        user = User(self._api, info, True)

        try:
            self._users.change_user(user)
            self._users.change_phone(chat_id, text)
            phone_code_hash = await self._users.require_code(chat_id)
            self._users.change_phone_code_hash(chat_id, phone_code_hash)

        except RuntimeError:
            emess = "Oops bad try access your account"
        except ValueError:
            emess = "Not correct message"
        except FloodWaitError as e:
            emess = f"Oops flood exception! Wait: {e.seconds} seconds"
        except OperationalError as e:
            self.logger.error(str(e))
            emess = "Oops database is fire!"
        else:
            self._users.save(chat_id)
        finally:
            await update.message.reply_text(emess)

    async def _send_now(self, update: Update, _: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        emess = "Well done"
        try:
            await self._users.checkin(chat_id)
        except cronaction.FloodError as e:
            emess = f"Flood detection! Wait {e.timeout}"
        except AuthKeyUnregisteredError as e:
            self.logger.error(str(e))
            emess = "Your token is not registered"
        except Exception as e:
            self.logger.error(str(e))
            emess = "Oops something went wrong"
        finally:
            await update.message.reply_text(emess)

    async def _delete(self, update: Update, _: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        await self._users.delete(chat_id)
        await update.message.reply_text("Your account was deleted!")

    async def _schedule(self, update: Update, _: ContextTypes.DEFAULT_TYPE):
        id = update.message.chat_id
        text = update.message.text

        if text.find(" ") == -1:
            sch = f"Your schedule {self._users.get_user(id)._info._schedule}"
            await update.message.reply_text(sch)
            return

        emess = "Done!"
        try:
            self._users.change_schedule(id, text)
        except CroniterNotAlphaError as e:
            self.logger.error(str(e))
            emess = "Error, schedule not change"
        except CroniterBadCronError as e:
            self.logger.error(str(e))
            emess = "Not valid range"
        except ValueError as e:
            self.logger.error(str(e))
            emess = str(e)
        except Exception as e:
            emess = "Oops unknown error"
            self.logger.error(e)
        else:
            self._users.save(id)

        await update.message.reply_text(emess)

    async def _raw_code(self, update: Update, _: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        chat_id = update.message.chat_id
        emess = "Success! Code complete!"

        users = self._users
        try:
            users.change_auth_code(chat_id, text)
            default_sch = "30 18 * * 6"
            users.change_schedule(chat_id, default_sch)
        except ValueError:
            emess = "Bad value of command"
        except KeyError:
            emess = "User not found, need first step /auth after send code"

        await update.message.reply_text(emess)

    async def _disable(self, update: Update, _: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        emess = "Your account is disable"
        try:
            self._users.disable(chat_id)
        except Exception as e:
            emess = "Oops somthing broke - " + str(e)

        await update.message.reply_text(emess)

    async def _enable(self, update: Update, _: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        emess = "Your account is enable"
        try:
            self._users.enable(chat_id)
        except Exception as e:
            emess = "Oops somthing broke - " + str(e)

        await update.message.reply_text(emess)

    def run(self) -> None:
        app = self._app
        commands = [
            ("start", self._start),
            ("help", self._help),
            ("auth", self._auth),
            ("code", self._raw_code),
            ("schedule", self._schedule),
            ("send", self._send_now),
            ("disable", self._disable),
            ("enable", self._enable),
            ("delete", self._delete),
        ]

        for name, func in commands:
            app.add_handler(CommandHandler(name, func))

        app.run_polling()
