import logging

from aiocron import crontab
from telethon import TelegramClient
from telethon.types import InputMediaGeoLive

from geolocation import Geolocation
from user import User


class CheckIn:
    logger: logging.Logger
    _to_username = '@poly_chess_bot'

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def send_live_location(self, user: TelegramClient) -> None:
        self.logger.debug('Send live location', str(user))
        geo = Geolocation()
        # Well... Ignore error from library tg, it's ok
        # Still send InputMediaGeoLive
        stream: InputMediaGeoLive = geo.get()
        await user.send_message(
            self._to_username,
            file=stream)

    def run(self, user: User):
        self.logger.debug('Run schedule for ', str(user))
        cron: str = user._info._schedule
        tg = user.instance_telegramclient()
        def func(): return self.send_live_location(tg)
        return crontab(cron, func=func, start=True)

    def pass_cron(self):
        schedule = '30 18 * * 6'

        def func():
            pass
        return crontab(schedule, func=func, start=False)
