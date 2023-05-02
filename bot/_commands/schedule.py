from .._action import Fakelocation
from .._commands import Command
from .._cron import Cron
from .._config import Config
from croniter.croniter import CroniterBadCronError, CroniterNotAlphaError
from telegram import Update
from telegram.ext import ContextTypes
from ..text import usertext as t


class Schedule(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self._config = Config()

    async def handle(self, update: Update, _: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        schedule = update.message.text
        user = self.bot.users[chat_id]

        if schedule.find(" ") == -1:
            await update.message.reply_text(
                t("cron_show_expression").format(
                    user.cron.expression if user.cron is not None else "None"
                )
            )
            return

        schedule = " ".join(schedule.split(" ")[1:])

        if user.location is None:
            await update.message.reply_text(t("need_location"))
            return

        if user.recipient is None:
            await update.message.reply_text(t("need_recipient"))
            return

        emess = t("cron_set_schedule")
        if user.cron is not None:
            user.cron.stop()

        try:
            user.cron = Cron(
                callback=Fakelocation(
                    self.bot.api, user.session, user.location, user.recipient
                ).execute,
                cron_expression=schedule,
                callback_timeout=user.cron.timeout
                if user.cron is not None
                else self._config.cron_timeout,
            )

            user.cron.start()
        except CroniterNotAlphaError | CroniterBadCronError as e:
            self.logger.error(str(e))
            emess = t("cron_invalid_expression")
        else:
            self.bot.db.save_user(self.bot.users[chat_id])

        await update.message.reply_text(emess)
