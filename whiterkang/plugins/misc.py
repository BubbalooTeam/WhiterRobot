# Copyright (C) 2023 BubbalooTeam

import requests
import html

from gpytranslate import Translator
from covid import Covid
from uuid import uuid4

from hydrogram import filters
from hydrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from whiterkang import WhiterX, Config
from whiterkang.helpers import tld, inline_handler, group_apps

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