# WhiterKang
#
# Copyright (C) 2023 BubbalooTeam

# Copyright (C) 2022 by fnixdev
#

__all__ = ["Config"]

import os
import heroku3
from dotenv import load_dotenv

if os.path.isfile("config.env"):
    load_dotenv("config.env")

class Config:
    AUTH_CHATS = set(
        [-1001569084822, -1001252486871, -1001412694056, -1001475334171, 1715384854, -1001517679518, -1001664402228]
    )  # chat permitidos
    if os.environ.get("AUTH_CHATS"):
        AUTH_CHATS.update(map(int, os.environ.get("AUTH_CHATS").split()))
    DEV_USERS = (  # lista de devs
        838926101,  # @fnixdev
        5374262463, # @junglivre
        1715384854, # @DaviTudo 
        1574959180, # @KlonoaSulista
        6419654672, # @lucmsilva
    )
    ADMINS = {}
    LASTFM_API_KEY = os.environ.get("LASTFM_API_KEY")
    API_ID = int(os.environ.get("API_ID"))
    RAM_CHECK = 1
    CPU_MHZ_CHECK = 1000
    STORAGE_CHECK = 20
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    GP_LOGS = int(os.environ.get("GP_LOGS"))
    REMOVE_BG_API_KEY = os.environ.get("REMOVE_BG_API_KEY")  
    DB_URI = os.environ.get("DATABASE_URL")
    TRIGGER = os.environ.get("TRIGGER", "/ !".split())
    WHITELIST_CHATS = set([])  # chat id aq
    EDIT_SLEEP_TIMEOUT = 5
    OWNER = int(1715384854)
    DOWN_PATH = "whiterkang/xcache/"
    SW_API = os.environ.get("SW_API")
    VT_API_KEY = os.environ.get("VT_API_KEY")
    PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
    GBAN_LOGS = os.environ.get("GBAN_LOGS")
    GSMARENA_API = os.environ.get("GSMARENA_API")
    
    HEROKU_API_KEY = os.environ.get("HEROKU_API_KEY")
    HEROKU_API_NAME = os.environ.get("HEROKU_API_NAME")

    heroku_app = heroku3.from_key(HEROKU_API_KEY).apps()[HEROKU_API_NAME] \
        if HEROKU_API_KEY and HEROKU_API_NAME else None


trg = Config.TRIGGER
