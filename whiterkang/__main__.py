# WhiterKang
# Copyright (C) 2022 KuuhakuTeam
#
# This file is based of < https://github.com/KuuhakuTeam/YuunaRobot/ >
# PLease read the GNU v3.0 License Agreement in 
# <https://www.github.com/KuuhakuTeam/YuunaRobot/blob/master/LICENSE/>.

import asyncio
import logging

from hydrogram import idle

from logging.handlers import RotatingFileHandler
from pymongo.errors import ConnectionFailure

from . import db_core, Config, remove_path
from .bot import WhiterX
from .helpers import load_language

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s - %(levelname)s] - %(name)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    handlers=[
                        RotatingFileHandler(
                            "WhiterX.log", maxBytes=2801100, backupCount=1),
                        logging.StreamHandler()
                    ])

logging.getLogger("hydrogram").setLevel(logging.WARNING)
logging.getLogger("hydrogram.parser.html").setLevel(logging.ERROR)
logging.getLogger("hydrogram.session.session").setLevel(logging.ERROR)


async def db_connect():
    """Check Mongo Client"""
    try:
        logging.info("Connecting to MongoDB.")
        await db_core.server_info()
        logging.info("DB Connected. Please Wait....")
    except (BaseException, ConnectionFailure) as e:
        logging.error("Failed to connect to database, exiting....")
        logging.debug(str(e))
        quit(1)


async def run_whiter():
    await db_connect()
    load_language()
    remove_path(Config.DOWN_PATH)
    await WhiterX.start()
    await idle()
    await WhiterX.stop()


if __name__ == "__main__" :
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run_whiter())
    except KeyboardInterrupt:
        pass
    except Exception as err:
        logging.error(err.with_traceback(None))
    finally:
        loop.stop()
