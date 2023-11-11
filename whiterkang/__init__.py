# WhiterKang
# Copyright (C) 2022 BubbalooTeam
#
# This file is based of < https://github.com/KuuhakuTeam/YuunaRobot/ >

import motor.motor_asyncio
import os

from .config import Config
from .bot import WhiterX, START_TIME

db_core = motor.motor_asyncio.AsyncIOMotorClient(Config.DB_URI)
db = db_core["megumin"]

def remove_path(path):
    try:
        os.remove(path)
    except BaseException:
        pass
