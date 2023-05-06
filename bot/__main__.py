import asyncio
import logging
import multiprocessing
import os
import sys

from ._config import Config
from ._db import DatabaseHandler

from .bot import Bot


def setup_logging():
    env_debug = os.environ.get("DEBUG", "false").lower()
    debug_flag = "--debug" in sys.argv or env_debug == "true"
    logging.basicConfig(level=logging.DEBUG if debug_flag else logging.WARN)


def get_root_path():
    root = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(root, "..")


def generate_bot(config: Config):
    db = DatabaseHandler(config.api, config.db_uri)
    return Bot(config.api, config.bot_token, db, config)


def start_bot(config: Config):
    bot = generate_bot(config)
    bot.run()


def start_cron():
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        asyncio.get_event_loop().stop()
        asyncio.get_event_loop().close()


def main():
    config = Config()
    setup_logging()
    cron_process = multiprocessing.Process(target=start_cron)
    bot_process = multiprocessing.Process(target=lambda: start_bot(config))
    cron_process.start()
    bot_process.start()


if __name__ == "__main__":
    main()
