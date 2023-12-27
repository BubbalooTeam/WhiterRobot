# Copyright (C) 2023 BubbalooTeam

import os


import requests
import html
import asyncio
import json

from gpytranslate import Translator
from covid import Covid
from uuid import uuid4
from datetime import datetime
from removebg import RemoveBg
from typing import Union


from hydrogram import filters
from hydrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from hydrogram.enums import ChatType
from hydrogram.errors import BadRequest

from whiterkang import WhiterX, Config
from whiterkang.helpers import tld, inline_handler, group_apps, weather_apikey, disableable_dec, scan_file, get_report, humanbytes, find_gp, add_gp

IMG_PATH = Config.DOWN_PATH + "WhiterOS-RemoveBG.png"

get_coords = "https://api.weather.com/v3/location/search"
url = "https://api.weather.com/v3/aggcommon/v3-wx-observations-current"


headers = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; M2012K11AG Build/SQ1D.211205.017)"
}

weather_url_thumb = "https://telegra.ph/file/abf3e0a8dd7ebd33f74e1.png"
translator_url_thumb = "https://telegra.ph/file/83402d7a4ca7b186a4281.jpg"

status_emojis = {
    0: "⛈",
    1: "⛈",
    2: "⛈",
    3: "⛈",
    4: "⛈",
    5: "🌨",
    6: "🌨",
    7: "🌨",
    8: "🌨",
    9: "🌨",
    10: "🌨",
    11: "🌧",
    12: "🌧",
    13: "🌨",
    14: "🌨",
    15: "🌨",
    16: "🌨",
    17: "⛈",
    18: "🌧",
    19: "🌫",
    20: "🌫",
    21: "🌫",
    22: "🌫",
    23: "🌬",
    24: "🌬",
    25: "🌨",
    26: "☁️",
    27: "🌥",
    28: "🌥",
    29: "⛅️",
    30: "⛅️",
    31: "🌙",
    32: "☀️",
    33: "🌤",
    34: "🌤",
    35: "⛈",
    36: "🔥",
    37: "🌩",
    38: "🌩",
    39: "🌧",
    40: "🌧",
    41: "❄️",
    42: "❄️",
    43: "❄️",
    44: "n/a",
    45: "🌧",
    46: "🌨",
    47: "🌩",
}

tr = Translator()

# See https://cloud.google.com/translate/docs/languages
# fmt: off
LANGUAGES = [
    "af", "sq", "am", "ar", "hy",
    "az", "eu", "be", "bn", "bs",
    "bg", "ca", "ceb", "zh", "co",
    "hr", "cs", "da", "nl", "en",
    "eo", "et", "fi", "fr", "fy",
    "gl", "ka", "de", "el", "gu",
    "ht", "ha", "haw", "he", "iw",
    "hi", "hmn", "hu", "is", "ig",
    "id", "ga", "it", "ja", "jv",
    "kn", "kk", "km", "rw", "ko",
    "ku", "ky", "lo", "la", "lv",
    "lt", "lb", "mk", "mg", "ms",
    "ml", "mt", "mi", "mr", "mn",
    "my", "ne", "no", "ny", "or",
    "ps", "fa", "pl", "pt", "pa",
    "ro", "ru", "sm", "gd", "sr",
    "st", "sn", "sd", "si", "sk",
    "sl", "so", "es", "su", "sw",
    "sv", "tl", "tg", "ta", "tt",
    "te", "th", "tr", "tk", "uk",
    "ur", "ug", "uz", "vi", "cy",
    "xh", "yi", "yo", "zu",
]
# fmt: on

async def get_tr_lang(m, text):
    chat_id = m.chat.id if isinstance(m, Message) else m.from_user.id
    if len(text.split()) > 0:
        lang = text.split()[0]
        if lang.split("-")[0] not in LANGUAGES:
            lang = await tld(chat_id, "language")
        if len(lang.split("-")) > 1 and lang.split("-")[1] not in LANGUAGES:
            lang = await tld(chat_id, "language")
    else:
        lang = await tld(chat_id, "language")
    return lang

def get_status_emoji(status_code: int) -> str:
    return status_emojis.get(status_code, "n/a")


@WhiterX.on_message(filters.command(["cota"], Config.TRIGGER))
async def cotas_money(c: WhiterX, m: Message):
    chat_id = m.chat.id
    if m.chat.type != ChatType.PRIVATE:
        if not await find_gp(chat_id):
            await add_gp(m)
    obting_info = await m.reply(await tld(chat_id, "COTA_PROGRESSING"))

    req = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,GBP-BRL,JPY-BRL,BTC-BRL,ETH-BRL,XRP-BRL,DOGE-BRL,ARS-BRL,RUB-BRL")

    res = req.json()

    cotacao_dolar = res['USDBRL']['bid']
    dat_dolar = res['USDBRL']['create_date']
    var_dolar = res['USDBRL']['varBid']
    cotacao_euro = res['EURBRL']['bid']
    dat_euro = res['EURBRL']['create_date']
    var_euro = res['EURBRL']['varBid']
    cotacao_btc = res['BTCBRL']['bid']
    dat_btc = res['BTCBRL']['create_date']
    var_btc = res['BTCBRL']['varBid']
    cotacao_iene = res['JPYBRL']['bid']
    dat_iene = res['JPYBRL']['create_date']
    var_iene = res['JPYBRL']['varBid']
    cotacao_doge = res['DOGEBRL']['bid']
    dat_doge = res['DOGEBRL']['create_date']
    var_doge = res['DOGEBRL']['varBid']
    cotacao_ars = res['ARSBRL']['bid']
    dat_ars = res['ARSBRL']['create_date']
    var_ars = res['ARSBRL']['varBid']
    cotacao_rub = res['RUBBRL']['bid']
    dat_rub = res['RUBBRL']['create_date']
    var_rub = res['RUBBRL']['varBid']

    await obting_info.delete()

    result = (await tld(chat_id, "COTED"))

    await m.reply_photo(photo="https://telegra.ph/file/d60e879db1cdba793a98c.jpg",
    caption=result.format(cotacao_dolar[:4], dat_dolar, var_dolar, cotacao_euro[:4], dat_euro, var_euro, cotacao_btc[:3], dat_btc, var_btc, cotacao_doge[:4], dat_doge, var_doge, cotacao_iene[:4], dat_iene, var_iene, cotacao_ars[:4], dat_ars, var_ars, cotacao_rub[:4], dat_rub, var_rub))

@WhiterX.on_inline_query(group=group_apps)
async def search_inline(c: WhiterX, q: InlineQuery):
    cmd = q.query.split(maxsplit=1)[0] if q.query else q.query

    res = inline_handler.search_cmds(cmd)
    if not res:
        return await q.answer(
            [
                InlineQueryResultArticle(
                    title="No results for {query}".format(query=cmd),
                    input_message_content=InputTextMessageContent(
                        "No results for {query}".format(query=cmd)
                    ),
                )
            ],
            cache_time=0,
        )
    articles = []
    for result in res:
        stripped_command = result["command"].split()[0]
        articles.append(
            InlineQueryResultArticle(
                id=uuid4(),
                title=result["command"],
                thumb_url=result["url_thumb"],
                description=result["txt_description"],
                input_message_content=InputTextMessageContent(
                    f"{html.escape(result['command'])}: {result['txt_description']}"
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="🌐 Run '{query}'".format(
                                    query=stripped_command
                                ),
                                switch_inline_query_current_chat=stripped_command,
                            )
                        ]
                    ]
                ),
            )
        )
    try:
        await q.answer(articles, cache_time=0)
    except Exception:
        return
    
@WhiterX.on_message(filters.command(["removebg", "rbg"], Config.TRIGGER))
@disableable_dec("removebg")
async def remove_background(c: WhiterX, m: Message):
    chat_id = m.chat.id
    if m.chat.type != ChatType.PRIVATE:
        if not await find_gp(chat_id):
            await add_gp(m)
    if not Config.REMOVE_BG_API_KEY:
        await m.reply(
            await tld(chat_id, "NO_API_RBG"),
            disable_web_page_preview=True,
        )
        return await c.send_err("<i>Error!!  There is no API-KEY of RemoveBg. Get <a href='https://www.remove.bg/b/background-removal-api'>Here</i>")

    replied = m.reply_to_message
    if (
        replied
        and replied.media
        and (
            replied.photo
            or (replied.document and "image" in replied.document.mime_type)
        )
    ):
        msg = await m.reply(await tld(chat_id, "COM_3"))
        start_t = datetime.now()
        if os.path.exists(IMG_PATH):
            os.remove(IMG_PATH)
        ##
        await msg.edit(await tld(chat_id, "DOWNLOAD_IMAGE_RBG"))
        ##
        await c.download_media(
            message=replied,
            file_name=IMG_PATH,
        )
        end_t = datetime.now()
        m_s = (end_t - start_t).seconds
        await msg.edit((await tld(chat_id, "IMAGE_SAVED_RBG")).format(m_s))
        # Cooking Image
        try:
            await msg.edit(await tld(chat_id, "IMAGE_UPLOADING_RBG"))
            rmbg = RemoveBg(Config.REMOVE_BG_API_KEY, "rbg_error.log")
            rmbg.remove_background_from_img_file(IMG_PATH)
            rbg_img_path = IMG_PATH + "_no_bg.png"
            start_t = datetime.now()
            await c.send_document(
                chat_id=m.chat.id,
                document=rbg_img_path,
                disable_notification=True,
            )
            await msg.delete()
            os.remove(IMG_PATH)
        except Exception as e:
            await msg.edit(await tld(chat_id, "ERROR_RBG") + "\n\n{e}")
            os.remove(IMG_PATH)
            return
    else:
        await m.reply(await tld(chat_id, "NO_REPLIED_RBG"))

@WhiterX.on_message(filters.command(["weather", "clima"], Config.TRIGGER))
@WhiterX.on_inline_query(filters.regex(r"^(clima|weather)"))
async def weather(c: WhiterX, m: Union[InlineQuery, Message]):
    text = m.text if isinstance(m, Message) else m.query
    chat_id = m.chat.id if isinstance(m, Message) else m.from_user.id
    if isinstance(m, Message) and m.chat.type != ChatType.PRIVATE:
        if not await find_gp(chat_id):
            await add_gp(m)
    if len(text.split(maxsplit=1)) == 1:
        try:
            if isinstance(m, Message):
                return await m.reply_text(await tld(chat_id, "WEATHER_NO_ARGS"))
            return await m.answer(
                [
                    InlineQueryResultArticle(
                        title=await tld(chat_id, "WEATHER_INLINE_NO_ARGS"),
                        thumb_url=weather_url_thumb,
                        input_message_content=InputTextMessageContent(
                            message_text=await tld(chat_id, "WEATHER_NO_ARGS"),
                        ),
                    )
                ],
                cache_time=0,
            )
        except BadRequest:
            return
    r = requests.get(
        get_coords,
        headers=headers,
        params=dict(
            apiKey=weather_apikey,
            format="json",
            language=await tld(chat_id, "WEATHER_LANGUAGE"),
            query=text.split(maxsplit=1)[1],
        ),
    )
    loc_json = r.json()
    if not loc_json.get("location"):
        try:
            if isinstance(m, Message):
                return await m.reply_text(await tld(chat_id, "WEATHER_LOCATION_NOT_FOUND"))

            return await m.answer(
                [
                    InlineQueryResultArticle(
                        title=await tld(chat_id, "WEATHER_LOCATION_NOT_FOUND"),
                        thumb_url=weather_url_thumb,
                        input_message_content=InputTextMessageContent(
                            message_text=await tld(chat_id, "WEATHER_LOCATION_NOT_FOUND"),
                        ),
                    )
                ],
                cache_time=0,
            )
        except BadRequest:
            return
    pos = f"{loc_json['location']['latitude'][0]},{loc_json['location']['longitude'][0]}"
    r = requests.get(
        url,
        headers=headers,
        params=dict(
            apiKey=weather_apikey,
            format="json",
            language=await tld(chat_id, "WEATHER_LANGUAGE"),
            geocode=pos,
            units=await tld(chat_id, "WEATHER_UNIT"),
        ),
    )
    res_json = r.json()

    obs_dict = res_json["v3-wx-observations-current"]

    res = (await tld(chat_id, "WEATHER_DETAILS")).format(
        location=loc_json["location"]["address"][0],
        temperature=obs_dict["temperature"],
        feels_like=obs_dict["temperatureFeelsLike"],
        air_humidity=obs_dict["relativeHumidity"],
        wind_speed=obs_dict["windSpeed"],
        overview=f"{get_status_emoji(obs_dict['iconCode'])} {obs_dict['wxPhraseLong']}",
    )

    try:
        if isinstance(m, Message):
            await m.reply_text(res)
        else:
            await m.answer(
                [
                    InlineQueryResultArticle(
                        title=loc_json["location"]["address"][0],
                        thumb_url=weather_url_thumb,
                        description=(await tld(chat_id, "WEATHER_INLINE_DETAILS")).format(
                            overview=f"{get_status_emoji(obs_dict['iconCode'])} {obs_dict['wxPhraseLong']}",
                            temperature=obs_dict["temperature"],
                            feels_like=obs_dict["temperatureFeelsLike"],
                            air_humidity=obs_dict["relativeHumidity"],
                            wind_speed=obs_dict["windSpeed"],
                        ),
                        input_message_content=InputTextMessageContent(
                            message_text=res,
                        ),
                    )
                ],
                cache_time=0,
            )
    except BadRequest:
        return
    

@WhiterX.on_message(filters.command("tr", Config.TRIGGER))
async def translate(c: WhiterX, m: Message):
    chat_id = m.chat.id
    if m.chat.type != ChatType.PRIVATE:
        if not await find_gp(chat_id):
            await add_gp(m)
    text = m.text[4:]
    lang = await get_tr_lang(m, text)

    text = text.replace(lang, "", 1).strip() if text.startswith(lang) else text

    if not text and m.reply_to_message:
        text = m.reply_to_message.text or m.reply_to_message.caption

    if not text:
        return await m.reply_text(await tld(chat_id, "NO_TEXT_TRANSLATE"))
        

    sent = await m.reply_text(await tld(chat_id, "TRANSLATING"))
    try:
        langs = {}

        if len(lang.split("-")) > 1:
            langs["sourcelang"] = lang.split("-")[0]
            langs["targetlang"] = lang.split("-")[1]
        else:
            langs["targetlang"] = lang

        trres = await tr.translate(text, **langs)
        text = trres.text

        res = html.escape(text)
        await sent.edit_text((await tld(chat_id, "TRANSLATED")).format(
                trres.lang, langs["targetlang"], res))
    except BadRequest:
        return await sent.delete()
    except Exception as e:
        await c.send_err(e)


@WhiterX.on_inline_query(filters.regex(r"^tr|translate"))
async def tr_inline(c: WhiterX, q: InlineQuery):
    try:
        uid = q.from_user.id
        to_tr = q.query.split(None, 2)[2]
        source_language = await tr.detect(q.query.split(None, 2)[2])
        to_language = q.query.lower().split()[1]
        translation = await tr(
            to_tr, sourcelang=source_language, targetlang=to_language
        )
        await q.answer(
            [
                InlineQueryResultArticle(
                    title=(await tld(uid, "LANG_TRANSLATE_INLINE")).format(
                        source_language, to_language
                    ),
                    thumb_url=translator_url_thumb,
                    description=f"{translation.text}",
                    input_message_content=InputTextMessageContent(
                        f"{translation.text}"
                    ),
                )
            ]
        )
    except IndexError:
        return
    
@WhiterX.on_message(filters.command("vt", Config.TRIGGER))
@disableable_dec("vt")
async def virus_total(c: WhiterX, m: Message):
    chat_id = m.chat.id
    if m.chat.type != ChatType.PRIVATE:
        if not await find_gp(chat_id):
            await add_gp(m)
    user_id = m.from_user.id
    FILE_PATH = f"{Config.DOWN_PATH}virustotal/"
    if not Config.VT_API_KEY:
        await m.reply(
            await tld(chat_id, "NO_API_VT"),
            disable_web_page_preview=True,
        )
        return await c.send_err("<i>You have to sign up on <code>virustotal.com</code> and get <code>API_KEY</code> and paste in <b>VT_API_KEY</b> var.")
    replied = m.reply_to_message
    if not (replied and replied.document):
        return await m.reply(await tld(chat_id, "VT_NO_REPLIED"))
    
    msg = await m.reply(await tld(chat_id, "COM_3"))

    size_of_file = replied.document.file_size
    if size_of_file > 32 * 1024 * 1024:
        await msg.edit(await tld(chat_id, "VT_BIG_FILE"))
        return
    
    await msg.edit(await tld(chat_id, "VT_DOWNLOADING"))
    dvt_loc = await c.download_media(
        message=replied,
        file_name=FILE_PATH,
    )
    dvt = os.path.join(FILE_PATH, os.path.basename(dvt_loc))
    
    await msg.edit((await tld(chat_id, "PROCESS_VT")).format(humanbytes(size_of_file)))

    response = await scan_file(dvt)
    os.remove(dvt)

    if response is False:
        await msg.edit(await tld(chat_id, "VT_NO_SCAN"))
        return
    
    await msg.edit(f"<code>{response.json()['verbose_msg']}</code>")
    sha1 = response.json()['resource']

    text = (await tld(chat_id, "VT_INFO_FILE")).format(dvt, humanbytes(size_of_file))

    await msg.edit(text)

    await asyncio.sleep(1)

    que_msg = "Your resource is queued for analysis"
    viruslist = []
    reasons = []
    pre_response = await get_report(sha1)
    response = pre_response.json()

    if "Invalid resource" in response.get('verbose_msg'):
        await msg.edit(response.get('verbose_msg'))
        return
    if response.get('verbose_msg') == que_msg:
        await msg.edit(f"<code>{que_msg}</code>")
        while response.get('verbose_msg') == que_msg:
            await asyncio.sleep(3)
            try:
                pre_response = await get_report(sha1)
                response = pre_response.json()
            except json.decoder.JSONDecodeError:
                await asyncio.sleep(3)
    try:
        report = response['scans']
        link = response['permalink']
    except Exception as e:
        await msg.edit(e)
        return
    for i in report:
        if report[i]['detected'] is True:
            viruslist.append("⛔️" + i)
            reasons.append('â¤ ' + report[i]['result'])
    if len(viruslist) > 0:
        names = '\n'.join(viruslist)
        reason = '\n'.join(reasons)
        await msg.edit((await tld(chat_id, "VT_THREATS")).format(len(viruslist), names, reason, link))
    else:
        await msg.edit(await tld(chat_id, "VT_FILE_IS_CLEAN"))


inline_handler.add_cmd("weather <location>", "Get weather information for the given location or city.", weather_url_thumb, aliases=["weather"])
inline_handler.add_cmd("tr <lang> <text>", "Translates text into the specified language.", translator_url_thumb, aliases=["translate", "tr"])

__help__ = True