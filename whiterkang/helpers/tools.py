import base64
import sys
import os
import uuid
import html
import re
import time
import httpx
import requests
import asyncio
import spamwatch
import logging
import json

from datetime import datetime, timedelta
from httpx import HTTPError
from typing import Any, Tuple, Callable, Union, Optional
from functools import partial, wraps
from math import floor
from PIL import Image, ImageOps
from io import BytesIO
from speedtest import Speedtest
from bs4 import BeautifulSoup
from hashlib import md5


from hydrogram import emoji
from hydrogram.enums import ChatMemberStatus, ChatType, MessageEntityType
from hydrogram.types import Message, User, CallbackQuery, ChatPrivileges

from whiterkang import WhiterX, Config, db
from . import tld

_BOT_ID = 0


timeout = httpx.Timeout(30, pool=None)
http = httpx.AsyncClient(http2=True, timeout=timeout)

weather_apikey = "8de2d8b3a93542c9a2d8b3a935a2c909"

WARNS = db["WARNS"]

#Map from gsmarena
MAP_CATEGORY = {
    "pt": {
        "Display": "Tela",
        "Platform": "Plataforma",
        "Memory": "Memória",
        "Main Camera": "Câmera principal",
        "Selfie camera": "Câmera frontal",
        "Sound": "Som",
        "Network": "Rede",
        "Battery": "Bateria",
        "Body": "Corpo",
        "Launch": "Lançado",
        "Comms": "Comunicações",
        "Features": "Características",
        "Misc": "Diversos",
        "Tests": "Testes"
    },
    "en": {
        "Display": "Display",
        "Platform": "Platform",
        "Memory": "Memory",
        "Main Camera": "Main camera",
        "Selfie camera": "Frontal camera",
        "Sound": "Sound",
        "Network": "Network",
        "Battery": "Battery",
        "Body": "Body",
        "Launch": "Launch",
        "Comms": "Comms",
        "Features": "Features",
        "Misc": "Misc",
        "Tests": "Tests"
    },
    "es": {
        "Display": "Pantalla",
        "Platform": "Plataforma",
        "Memory": "Memoria",
        "Main Camera": "Cámara principal",
        "Selfie camera": "Cámara frontal",
        "Sound": "Sonido",
        "Network": "Red",
        "Battery": "Batería",
        "Body": "Cuerpo",
        "Launch": "Lanzamiento",
        "Comms": "Comunicaciones",
        "Features": "Características",
        "Misc": "Varios",
        "Tests": "Pruebas"
    }
}

MAP_INFO = {
    "pt": {
        "Technology": "Tecnologia",
        "2G bands": "Bandas 2G",
        "3G bands": "Bandas 3G",
        "4G bands": "Bandas 4G",
        "Speed": "Velocidade",
        "Announced": "Anunciado",
        "Status": "Status",
        "Dimensions": "Dimensões",
        "Weight": "Peso",
        "SIM": "Cartão SIM",
        "Size": "Tamanho",
        "Resolution": "Resolução",
        "OS": "Sistema Operacional",
        "Chipset": "Processador",
        "CPU": "CPU",
        "GPU": "GPU",
        "Card slot": "Slot de Cartão",
        "Internal": "Interna",
        "Single": "Principal",
        "Dual": "Dupla",
        "Triple": "Tripa",
        "Quadruple": "Quadrupla",
        "Features": "Recursos",
        "Video": "Vídeo",
        "Loudspeaker ": "Alto-falante",
        "3.5mm jack ": "Conector 3.5mm",
        "WLAN": "Wi-Fi",
        "Bluetooth": "Bluetooth",
        "Positioning": "Posicionamento",
        "NFC": "NFC",
        "Radio": "Rádio",
        "USB": "USB",
        "Sensors": "Sensores",
        "Type": "Tipo",
        "Colors": "Cores",
        "Models": "Modelos",
        "SAR": "Taxa de Absorção",
        "SAR EU": "Taxa de Absorção na União Europeia",
        "Price": "Preço",
        "Charging": "Potência de Carregamento",
        "Performance": "Desempenho",
        "Battery life": "Vida da Bateria",
        "Audio quality": "Qualidade Sonora",
        "Display": "Tela"
    },
    "en": {
        "Technology": "Technology",
        "2G bands": "2G bands",
        "3G bands": "3G bands",
        "4G bands": "4G bands",
        "Speed": "Speed",
        "Announced": "Announced",
        "Status": "Status",
        "Dimensions": "Dimensions",
        "Weight": "Weight",
        "SIM": "SIM Card",
        "Size": "Size",
        "Resolution": "Resolution",
        "OS": "Operating System",
        "Chipset": "Chipset",
        "CPU": "CPU",
        "GPU": "GPU",
        "Card slot": "Card Slot",
        "Internal": "Internal",
        "Single": "Single",
        "Dual": "Dual",
        "Triple": "Triple",
        "Quadruple": "Quadruple",
        "Features": "Features",
        "Video": "Video",
        "Loudspeaker": "Loudspeaker",
        "3.5mm jack": "3.5mm Jack",
        "WLAN": "Wi-Fi",
        "Bluetooth": "Bluetooth",
        "Positioning": "Positioning",
        "NFC": "NFC",
        "Radio": "Radio",
        "USB": "USB",
        "Sensors": "Sensors",
        "Type": "Type",
        "Colors": "Colors",
        "Models": "Models",
        "SAR": "SAR",
        "SAR EU": "SAR EU",
        "Price": "Price",
        "Charging": "Charging Power",
        "Performance": "Performance",
        "Battery life": "Battery Life",
        "Audio quality": "Audio Quality",
        "Display": "Display"
    },
    "es": {
        "Technology": "Tecnología",
        "2G bands": "Bandas 2G",
        "3G bands": "Bandas 3G",
        "4G bands": "Bandas 4G",
        "Speed": "Velocidad",
        "Announced": "Anunciado",
        "Status": "Estado",
        "Dimensions": "Dimensiones",
        "Weight": "Peso",
        "SIM": "Tarjeta SIM",
        "Size": "Tamaño",
        "Resolution": "Resolución",
        "OS": "Sistema Operativo",
        "Chipset": "Procesador",
        "CPU": "CPU",
        "GPU": "GPU",
        "Card slot": "Ranura para tarjeta",
        "Internal": "Almacenamiento interno",
        "Single": "Individual",
        "Dual": "Doble",
        "Triple": "Triple",
        "Quadruple": "Cuádruple",
        "Features": "Características",
        "Video": "Video",
        "Loudspeaker": "Altavoz",
        "3.5mm jack": "Conector de 3.5mm",
        "WLAN": "Wi-Fi",
        "Bluetooth": "Bluetooth",
        "Positioning": "Posicionamiento",
        "NFC": "NFC",
        "Radio": "Radio",
        "USB": "USB",
        "Sensors": "Sensores",
        "Type": "Tipo",
        "Colors": "Colores",
        "Models": "Modelos",
        "SAR": "Tasa de absorción",
        "SAR EU": "Tasa de absorción en la Unión Europea",
        "Price": "Precio",
        "Charging": "Poder de Carga",
        "Performance": "Actuación",
        "Battery life": "Vida de la Batería",
        "Audio quality": "Calidad de Audio",
        "Display": "Pantalla"
    }
}

#anilist
MANGA_QUERY = """
query ($search: String, $page: Int) {
  Page (perPage: 1, page: $page) {
    pageInfo {
      total
    }
    media (search: $search, type: MANGA) {
      id
      title {
        romaji
        english
        native
      }
      format
      countryOfOrigin
      source (version: 2)
      status
      description(asHtml: true)
      chapters
      isFavourite
      mediaListEntry {
        status
        score
        id
      }
      volumes
      averageScore
      siteUrl
      isAdult
    }
  }
}
"""

PERMISSIONS_STRING = {
    "can_change_info": "NO_CHANGEINFO_PERM",
    "can_delete_messages": "NO_DELETEMSGS_PERM",
    "can_restrict_members": "NO_RESTRICT_PERM",
    "can_invite_users": "NO_INVITEUSER_PERM",
    "can_pin_messages": "NO_PINMSGS_PERM",
    "can_manage_video_chats": "NO_MANAGEVIDEO_PERM",
    "can_promote_members": "NO_PROMOTE_MEMBERS_PERM",
}


def time_formatter(seconds: float) -> str:
    """tempo"""
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + "d, ") if days else "")
        + ((str(hours) + "h, ") if hours else "")
        + ((str(minutes) + "m, ") if minutes else "")
        + ((str(seconds) + "s, ") if seconds else "")
    )
    return tmp[:-2]


def is_dev(user_id: int) -> bool:
    """retorna se é dev ou não"""
    return user_id in Config.DEV_USERS


async def is_self(user_id: int) -> bool:
    """retorna se usuario é assistente ou não"""
    global _BOT_ID  # pylint: disable=global-statement
    if not _BOT_ID:
        _BOT_ID = (await WhiterX.get_me()).id
    return user_id == _BOT_ID

async def is_admin(chat_id: int, user_id: int, check_devs: bool = False) -> bool:
    """checa admin no chat"""
    if check_devs and is_dev(user_id):
        return True
    check_status = await WhiterX.get_chat_member(chat_id=chat_id, user_id=user_id)
    admin_strings = [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    if check_status.status not in admin_strings:
        return False
    else:
        return True

async def check_bot_rights(chat_id: int, rights: str) -> bool:
    """check permissions WhiterX"""
    global _BOT_ID  # pylint: disable=global-statement
    if not _BOT_ID:
        _BOT_ID = (await WhiterX.get_me()).id
    bot_ = await WhiterX.get_chat_member(chat_id, _BOT_ID)
    if bot_.status == ChatMemberStatus.ADMINISTRATOR:
        if getattr(bot_.privileges, rights, None):
            return True
        return False
    return False

def humanbytes(size: float) -> str:
    """humanize size"""
    if not size:
        return ""
    power = 1024
    t_n = 0
    power_dict = {0: " ", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
    while size > power:
        size /= power
        t_n += 1
    return "{:.2f} {}B".format(size, power_dict[t_n])


def encode_to_base64_string(msg: str) -> str:
    msg_bytes = msg.encode("utf-8")
    base64_bytes = base64.b64encode(msg_bytes)
    return base64_bytes.decode("utf-8")


def decode_to_base64_string(msg: str) -> str:
    msg_bytes = msg.encode("utf-8")
    base64_bytes = base64.b64decode(msg_bytes)
    return base64_bytes.decode("utf-8")


async def extract_time(msg, time_val):
    if any(time_val.endswith(unit) for unit in ("m", "h", "d")):
        unit = time_val[-1]
        time_num = time_val[:-1]  # type: str
        if not time_num.isdigit():
            await msg.reply("`Quantidade de tempo específicada é inválida.`")
            return

        if unit == "m":
            bantime = datetime.now() + timedelta(minutes=int(time_num))
        elif unit == "h":
            bantime = datetime.now() + timedelta(hours=int(time_num))
        elif unit == "d":
            bantime = datetime.now() + timedelta(days=int(time_num))  
        else:
            await msg.reply("`Existe outra unidade de tempo que você conhece ..?`")
            return
        return bantime
    else:
        await msg.reply("`Eu preciso que você informe um tempo (m, h ou d)`")
        return


async def cssworker_url(target_url: str):
    url = "https://screenshotlayer.com"

    try:
        res = await http.get(url)
        soup = BeautifulSoup(res.text(), "html.parser")
        scl_secret = soup.findAll("input")[1]["value"]
        key = md5((target_url + scl_secret).encode()).hexdigest()
        resp = f"https://screenshotlayer.com/php_helper_scripts/scl_api.php?secret_key={key}&url={target_url}"
        return resp
    except HTTPError:
        return None


def cleanhtml(raw_html):
    cleanr = re.compile("<.*?>")
    cleantext = re.sub(cleanr, "", raw_html)
    return cleantext


def escape_definition(definition):
    for key, value in definition.items():
        if isinstance(value, str):
            definition[key] = html.escape(cleanhtml(value))
    return definition

async def unwarn_bnt(gid: int, user_id: int):
    await WARNS.delete_one({"chat_id": gid, "user_id": user_id})

def aiowrap(func: Callable) -> Callable:
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


def get_progress(percentage: int):
    progress_bar = (
        "[" + "==" * floor(15 * percentage / 100) +
        "\\" * floor(15 * (1 - percentage / 100)) + "]"
    )
    return progress_bar


def gsmarena_tr_category(category: str, lang: str):
    tr_ = MAP_CATEGORY.get(lang, "en").get(category, f"{category}")
    return tr_
    


def gsmarena_tr_info(info: str, lang: str):
    tr_ = MAP_INFO.get(lang, "en").get(info, f"{info}")
    return tr_

def resize_image(file: str) -> BytesIO:
    im = Image.open(file)
    im = ImageOps.contain(im, (512, 512), method=Image.LANCZOS)
    image = BytesIO()
    image.name = "sticker.png"
    im.save(image, "PNG")
    return image


async def convert_video(file: str) -> str:
    process = await asyncio.create_subprocess_exec(
        *[
            "ffmpeg",
            "-loglevel",
            "quiet",
            "-i",
            file,
            "-t",
            "00:00:03",
            "-vf",
            "fps=30",
            "-c:v",
            "vp9",
            "-b:v:",
            "500k",
            "-preset",
            "ultrafast",
            "-s",
            "512x512",
            "-y",
            "-an",
            "-f",
            "webm",
            "pipe:%i" % sys.stdout.fileno(),
        ],
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )

    (stdout, stderr) = await process.communicate()
    os.remove(file)
    # it is necessary to delete the video because
    # ffmpeg used a saved file and not bytes,
    # unfortunately it is not possible to convert
    # the video or gif to webm in the telegram
    # sticker video requirements with ffmpeg input in bytes
    return BytesIO(stdout)


    if webm_video != filename:
        os.remove(filename)
    return webm_video

def get_emoji_regex():
    e_list = [
        getattr(emoji, e).encode("unicode-escape").decode("ASCII")
        for e in dir(emoji)
        if not e.startswith("_")
    ]
    # to avoid re.error excluding char that start with '*'
    e_sort = sorted([x for x in e_list if not x.startswith("*")], reverse=True)
    # Sort emojis by length to make sure multi-character emojis are
    # matched first
    pattern_ = f"({'|'.join(e_sort)})"
    return re.compile(pattern_)

async def aexec(code, client, message):
    exec(
        "async def __aexec(client, message): "
        + "".join(f"\n {l_}" for l_ in code.split("\n"))
    )
    return await locals()["__aexec"](client, message)

async def search_yt(query):
    page = (
        await http.get(
            "https://www.youtube.com/results",
            params=dict(search_query=query, pbj="1"),
            headers={
                "x-youtube-client-name": "1",
                "x-youtube-client-version": "2.20200827",
            },
        )
    ).json()
    list_videos = []
    for video in page[1]["response"]["contents"]["twoColumnSearchResultsRenderer"][
        "primaryContents"
    ]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"]:
        if video.get("videoRenderer"):
            dic = {
                "title": video["videoRenderer"]["title"]["runs"][0]["text"],
                "url": "https://www.youtube.com/watch?v="
                + video["videoRenderer"]["videoId"],
            }
            list_videos.append(dic)
    return list_videos

async def get_ytthumb(videoid: str):
    thumb_quality = [
        "maxresdefault.jpg",  # Best quality
        "hqdefault.jpg",
        "sddefault.jpg",
        "mqdefault.jpg",
        "default.jpg",  # Worst quality
    ]
    thumb_link = "https://i.imgur.com/4LwPLai.png"
    for qualiy in thumb_quality:
        link = f"https://i.ytimg.com/vi/{videoid}/{qualiy}"
        if requests.get(link).status_code == 200:
            thumb_link = link
            break
    return thumb_link
    
def rand_key():
    return str(uuid.uuid4())[:8]

EMOJI_PATTERN = get_emoji_regex()

spamwatch_api = Config.SW_API
if spamwatch_api == "None":
    sw = None
    logging.warning("SpamWatch API key is missing! Check your config.env.")
else:
    try:
        sw = spamwatch.Client(spamwatch_api)
    except Exception:
        sw = None
        
async def get_target_user(c: WhiterX, m: Message) -> User:
    if m.reply_to_message:
        return m.reply_to_message.from_user
    msg_entities = m.entities[1] if m.text.startswith("/") else m.entities[0]
    return await c.get_users(
        msg_entities.user.id
        if msg_entities.type == MessageEntityType.TEXT_MENTION
        else int(m.command[1])
        if m.command[1].isdecimal()
        else m.command[1]
    )

async def get_reason_text(c: WhiterX, m: Message) -> Message:
    reply = m.reply_to_message
    spilt_text = m.text.split

    if not reply and len(spilt_text()) >= 3:
        return spilt_text(None, 2)[2]
    if reply and len(spilt_text()) >= 2:
        return spilt_text(None, 1)[1]

    return None

async def check_perms(
    m: Union[CallbackQuery, Message],
    permissions: Optional[ChatPrivileges] = None,
    complain_missing_perms: bool = True,
) -> bool:
    if isinstance(m, CallbackQuery):
        sender = partial(m.answer, show_alert=True)
        chat = m.message.chat
    else:
        sender = m.reply_text
        chat = m.chat
    # TODO: Cache all admin permissions in db.
    user = await chat.get_member(m.from_user.id)
    if user.status == ChatMemberStatus.OWNER:
        return True

    # No permissions specified, accept being an admin.
    if not permissions and user.status == ChatMemberStatus.ADMINISTRATOR:
        return True
    if user.status != ChatMemberStatus.ADMINISTRATOR:
        if complain_missing_perms:
            await sender(await tld(chat.id, "USER_NO_ADMIN"))
        return False

    missing_perms = [
        perm
        for perm, value in permissions.__dict__.items()
        if value and not getattr(user.privileges, perm)
    ]

    if not missing_perms:
        return True
    if complain_missing_perms:
        try:
            strmap_perm = ''.join(c for c in missing_perms if c not in '[]')
            string = PERMISSIONS_STRING[strmap_perm]
        except Exception as e:
            await sender(e)
        await sender((await tld(chat.id, string)))
    return False

async def scan_file(path: str) -> requests.Response:
    """ scan file """
    url = 'https://www.virustotal.com/vtapi/v2/file/scan'
    path_name = path.split('/')[-1]

    params = {'apikey': Config.VT_API_KEY}
    files = {
        'file': (path_name, open(path, 'rb'))  # skipcq
    }
    return await http.post(url, files=files, params=params)


async def get_report(sha1: str) -> requests.Response:
    """ get report of files """
    url = 'https://www.virustotal.com/vtapi/v2/file/report'
    params = {
        'apikey': Config.VT_API_KEY, 'resource': sha1, 'allinfo': 'False'
    }
    return await http.get(url, params=params)

async def speedtst_performer(msg): 
    test = Speedtest()
    bs = test.get_best_server()
    await msg.edit("<code>Performing test from Download...</code>")
    dl = round(test.download() / 1024 / 1024, 2)
    await msg.edit("<code>Performing test from Upload...</code>")
    ul = round(test.upload() / 1024 / 1024, 2)
    await msg.edit("<code>Getting some informations...</code>")
    test.results.share()
    result = test.results.dict()
    name = result["server"]["name"]
    host = bs["sponsor"]
    ping = bs["latency"]
    isp = result["client"]["isp"]   
    country = result["server"]["country"] 
    cc = result["server"]["cc"]
    path = (result["share"])
    return dl, ul, name, host, ping, isp, country, cc, path