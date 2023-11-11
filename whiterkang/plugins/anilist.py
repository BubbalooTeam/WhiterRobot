# Copyright (C) 2023 BubbalooTeam
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from whiterkang import WhiterX, Config
from whiterkang.helpers import http, MANGA_QUERY, input_str, tld

async def return_anilist_data(query, vars_):
    url_ = "https://graphql.anilist.co"
    post_conn = await http.post(
        url_, json={"query": query, "variables": vars_}
    ) 
    json_data = await post_conn.json()
    return json_data


@WhiterX.on_message(filters.command("manga", Config.TRIGGER))
async def manga_search(c: WhiterX, m: Message):
    query = input_str(m)
    if not query:
        await m.reply(await tld(m.chat.id, "ANILIST_NOT_QUERY"))
        return
    var = {"search": query, "asHtml": True}
    result = await return_anilist_data(MANGA_QUERY, var)
    error = result.get("errors")
    if error:
        error_sts = error[0].get("message")
        await m.reply("{error_sts}".format(error_sts=error_sts))
        return
    if len(result["data"]["Page"]["media"]) == 0:
        return [f"No results Found"]
    data = result["data"]["Page"]["media"][0]
    idm = data.get("id")
    romaji = data["title"]["romaji"]
    data["title"]["english"]
    native = data["title"]["native"]
    status = data.get("status")
    description = data.get("description")
    volumes = data.get("volumes")
    chapters = data.get("chapters")
    score = data.get("averageScore")
    site_url = data.get("siteUrl")
    format_ = data.get("format")
    data.get("countryOfOrigin")
    source = data.get("source")
    data.get("isFavourite")
    data.get("isAdult")
    name = f"""[🇯🇵]<b>{romaji}</b>
        {native}"""
    finals_ = f"{name}\n\n"
    finals_ += f"➤ <b>ID:</b> <code>{idm}</code>\n"
    finals_ += f"➤ <b>STATUS:</b> <code>{status}</code>\n"
    finals_ += f"➤ <b>VOLUMES:</b> <code>{volumes}</code>\n"
    finals_ += f"➤ <b>CHAPTERS:</b> <code>{chapters}</code>\n"
    finals_ += f"➤ <b>SCORE:</b> <code>{score}</code>\n"
    finals_ += f"➤ <b>FORMAT:</b> <code>{format_}</code>\n"
    finals_ += f"➤ <b>SOURCE:</b> <code>{source}</code>\n"
    finals_ += f"\n<b>Description:</b> <code>{description}</code>\n\n"
    pic = f"https://img.anili.st/media/{idm}"
    buttons = InlineKeyboardMarkup(
        [[InlineKeyboardButton(await tld(m.chat.id, "ANILIST_VISIT_WEB"), url=site_url)]]
    )
    await c.send_photo(
        chat_id=m.chat.id, photo=pic, caption=finals_, reply_markup=buttons
    )

