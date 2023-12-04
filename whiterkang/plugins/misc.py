# Copyright (C) 2023 BubbalooTeam

import os


import requests
import html

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
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from hydrogram.errors import BadRequest

from whiterkang import WhiterX, Config
from whiterkang.helpers import tld, inline_handler, group_apps, weather_apikey, disableable_dec

IMG_PATH = Config.DOWN_PATH + "WhiterOS-RemoveBG.png"

get_coords = "https://api.weather.com/v3/location/search"
url = "https://api.weather.com/v3/aggcommon/v3-wx-observations-current"


headers = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; M2012K11AG Build/SQ1D.211205.017)"
}

url_thumb = "https://telegra.ph/file/abf3e0a8dd7ebd33f74e1.png"

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


def get_status_emoji(status_code: int) -> str:
    return status_emojis.get(status_code, "n/a")


@WhiterX.on_message(filters.command(["cota"], Config.TRIGGER))
async def cotas_money(_, message: Message):
    obting_info = await message.reply(f"<i>Obtendo informações sobre as moedas...</i>")

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

    result = "<b>Cotação das moedas:</b>\n\n💵 <b>Dólar:</b> R$ <code>{}</code>\n🗓 <b>Data:</b>  <code>{}</code>\n📊 <b>Variação:</b> <code>{}</code>\n\n💵 <b>Euro:</b> R$ <code>{}</code>\n🗓 <b>Data:</b>  <code>{}</code>\n📊 <b>Variação:</b> <code>{}</code>\n\n💵 <b>BTC:</b> R$ <code>{}</code>\n🗓 <b>Data:</b>  <code>{}</code>\n📊 <b>Variação:</b> <code>{}</code>\n\n💵 <b>DOGE:</b> R$ <code>{}</code>\n🗓 <b>Data:</b> <code>{}</code>\n📊 <b>Variação:</b> <code>{}</code>\n\n💵 <b>Iene:</b> R$ <code>{}</code>\n🗓 <b>Data:</b> <code>{}</code>\n📊 <b>Variação:</b> <code>{}</code>\n\n💵 <b>Peso Argentino:</b> R$ <code>{}</code>\n🗓 <b>Data:</b> <code>{}</code>\n📊 <b>Variação:</b> <code>{}</code>\n\n💵 <b>Ruplo Russo:</b> R$ <code>{}</code>\n🗓 <b>Data:</b> <code>{}</code>\n📊 <b>Variação:</b> <code>{}</code>"

    await message.reply_photo(photo="https://telegra.ph/file/d60e879db1cdba793a98c.jpg",
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
        await msg.edit((await tld(chat_id, "IMAGE_SAVED_RBG").format(m_s)))
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
        except Exception:
            await m.reply(await tld(chat_id, "ERROR_RBG"))
            os.remove(IMG_PATH)
            return
    else:
        await m.reply(await tld(chat_id, "NO_REPLIED_RBG"))

@WhiterX.on_message(filters.command(["weather", "clima"], prefixes=["/", "!"]))
@WhiterX.on_inline_query(filters.regex(r"^(clima|weather)"))
async def weather(c: WhiterX, m: Union[InlineQuery, Message]):
    text = m.text if isinstance(m, Message) else m.query
    chat_id = m.chat.id if isinstance(m, Message) else m.from_user.id
    if len(text.split(maxsplit=1)) == 1:
        try:
            if isinstance(m, Message):
                return await m.reply_text(await tld(chat_id, "WEATHER_NO_ARGS"))
            return await m.answer(
                [
                    InlineQueryResultArticle(
                        title=await tld(chat_id, "WEATHER_INLINE_NO_ARGS"),
                        thumb_url=url_thumb,
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
                        thumb_url=url_thumb,
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
                        thumb_url=url_thumb,
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

inline_handler.add_cmd("weather <location>", "Get weather information for the given location or city.", url_thumb, aliases=["weather"])