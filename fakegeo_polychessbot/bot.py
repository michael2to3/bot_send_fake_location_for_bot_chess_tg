import logging
from croniter.croniter import CroniterBadCronError, CroniterNotAlphaError

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from _db import DatabaseHandler
from _commands import Start, Help, Auth, Code, Schedule, Send, Delete, Disable, Enable
from _type import ApiApp, User


class Bot:
    logger: logging.Logger
    _api: ApiApp
    _app: Application
    _users: list[User]
    _db: DatabaseHandler

    def __init__(self, api: ApiApp, token: str, db: DatabaseHandler):
        self.logger = logging.getLogger(__name__)
        self._app = Application.builder().token(token).build()
        self._api = api
        self._db = db
        self._users = list(db.load_all_users())

    async def _handle_command(
        self, command: str, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        if update.message is None:
            self.logger.error(f"Message is None in command: {command}")
            return

        command = update.message.text.split(" ")[0].lstrip("/")

        handlers = {
            "start": Start(self),
            "help": Help(self),
            "auth": Auth(self),
            "code": Code(self),
            "schedule": Schedule(self),
            "send": Send(self),
            "disable": Disable(self),
            "enable": Enable(self),
            "delete": Delete(self),
        }

        handler = handlers.get(command)
        if handler:
            try:
                await handler.handle(update, context)
            except Exception as e:
                self.logger.error(f"Error while handling the command: {command}, {e}")
                await update.message.reply_text(
                    f"Oops! An error occurred while handling the command: {command}."
                )
        else:
            self.logger.warn(f"Unknown command: {command}")
            await update.message.reply_text(f"Unknown command: {command}")

    def run(self) -> None:
        app = self._app
        commands = [
            "start",
            "help",
            "auth",
            "code",
            "schedule",
            "send",
            "disable",
            "enable",
            "delete",
        ]

        for command in commands:
            app.add_handler(
                CommandHandler(
                    command, lambda u, c: self._handle_command(command, u, c)
                )
            )
        app.run_polling()
