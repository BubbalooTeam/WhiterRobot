#CREDITS https://github.com/ruizlenato/SmudgeLord/blob/rewrite/smudge/plugins/videos.py
import io
import os
import re
import random
import shutil
import tempfile
import datetime
import asyncio
import contextlib
import filetype

from yt_dlp import YoutubeDL
from urllib.parse import unquote
from youtubesearchpython.__future__ import VideosSearch
from bs4 import BeautifulSoup

from hydrogram import filters, enums
from hydrogram.errors import BadRequest, FloodWait, Forbidden, MediaEmpty, MessageNotModified, UserNotParticipant
from hydrogram.raw.types import InputMessageID
from hydrogram.raw.functions import channels, messages
from hydrogram.types import (
    Message, 
    CallbackQuery, 
    InlineQuery, 
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InputMediaVideo, 
    InputMediaPhoto,
    InputMediaAudio,
    InputTextMessageContent, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ChatPrivileges,
)
from hydrogram.enums import ChatType, ChatAction 


from whiterkang import WhiterX, Config 
from whiterkang.helpers import humanbytes, tld, csdl, cisdl, tsdl, tisdl, DownloadMedia, extract_info, http, is_admin, add_user, find_user, search_yt, require_admin, disableable_dec, get_ytthumb, rand_key, get_download_button, SearchResult, inline_handler


YOUTUBE_REGEX = re.compile(
    r"(?m)http(?:s?):\/\/(?:www\.)?(?:music\.)?youtu(?:be\.com\/(watch\?v=|shorts/|embed/)|\.be\/|)(?P<id>([\w\-\_]{11}))(&(amp;)?‌​[\w\?‌​=]*)?"
)

SDL_REGEX_LINKS = r"(?:htt.+?//)?(?:.+?)?(?:instagram|twitter|x|tiktok|threads).(com|net)\/(?:\S*)"

MAX_FILESIZE = 2000000000

YT_VAR = {}

iytdl_url_thumb = "https://telegra.ph/file/adba42039e95dae5559aa.png"

@WhiterX.on_message(filters.command("ytdl", Config.TRIGGER))
@disableable_dec("ytdl")
async def ytdlcmd(c: WhiterX, m: Message):
    user = m.from_user.id
    chat_id = m.chat.id
    scroll = False

    if not await find_user(user):
        await add_user(user)

    if m.reply_to_message and m.reply_to_message.text:
        url = m.reply_to_message.text
    elif len(m.command) > 1:
        url = m.text.split(None, 1)[1]
    else:
        await m.reply_text(await tld(m.chat.id, "NO_ARGS_YT"))
        return

    ydl = YoutubeDL({"noplaylist": True})

    rege = YOUTUBE_REGEX.match(url)

    if not rege:
        yt = await VideosSearch(url).next()
        if yt["result"] == []:
            return await m.reply(f"No result found for `{url}`")
        inf = yt["result"]
        scroll = True
        try:
            yt = yt["result"][0]
        except IndexError:
            return
    else:
        yt = await extract_info(ydl, rege.group(), download=False)
        scroll = False

    #Generate a  random code
    key_search = rand_key()

    keyboard = [
        [
            InlineKeyboardButton(
                await tld(m.chat.id, "SONG_BNT"),
                callback_data=f'_yta.{yt["id"]}|a|{user}|{chat_id}|{key_search}|{scroll}'
            ),
            InlineKeyboardButton(
                await tld(m.chat.id, "VID_BNT"),
                callback_data=f'_ytv.{yt["id"]}|v|{user}|{chat_id}|{key_search}|{scroll}'
            ),
        ]
    ]

    
    if " - " in yt["title"]:
        performer, title = yt["title"].rsplit(" - ", 1)
    else:
        try:
            performer = yt.get("channel", {}).get("name", "N/A")
        except AttributeError:
            performer = None
        title = yt["title"]


    if scroll == True:
        # Save infos
        YT_VAR[key_search] = inf
        #Add a scroll buttons
        keyboard += [
            [
                InlineKeyboardButton(
                    f"1/{len(inf)}",
                    callback_data=f'yt_scroll|{key_search}|{user}|1|{chat_id}'
                ),
            ],
        ]

    thumb_ = await get_ytthumb(yt["id"])

    text = f"🎧 <b>{performer}</b> - <i>{title}</i>\n\n"
    text += f"⏳ <code>{yt.get('duration', None)}</code>\n\n"
    text += f"🎥 <b> Views:</b> <code>{yt.get('viewCount', {}).get('short', 'N/A')}</code>\n\n"
    text += f"⏰ <code>{yt.get('publishedTime', None)}</code>"

    await m.reply_photo(photo=thumb_, caption=text, reply_markup=InlineKeyboardMarkup(keyboard))

@WhiterX.on_inline_query(r"^(iytdl|ytdl)")
async def iytdl_handler(c: WhiterX, iq: InlineQuery):
    results = []
    scroll = False
    user_id = iq.from_user.id
    query = iq.query
    if len(query.split(maxsplit=1)) == 1:
        return await iq.answer(
            [
                InlineQueryResultArticle(
                    title=await tld(user_id, "NO_ARGS_YT"),
                    thumb_url=iytdl_url_thumb,
                    input_message_content=InputTextMessageContent(
                        message_text=await tld(user_id, "NO_ARGS_YT"),
                    ),
                )
            ],
            cache_time=0,
        )
    query = query.split(maxsplit=1)[1]
    ydl = YoutubeDL({"noplaylist": True})
    match = YOUTUBE_REGEX.match(query)
    found_ = False
    if match is None:
        yt = await VideosSearch(query).next()
        if yt["result"] == []:
            found_ = False
        inf = yt["result"]
        scroll = True
        try:
            yt = yt["result"][0]
            found_ = True
        except (KeyError, IndexError):
            return
    else:
        yt = await extract_info(ydl, match.group(), download=False)
        scroll = False
        found_ = True 

    #Generate a  random code
    key_search = rand_key()

    keyboard = [
        [
            InlineKeyboardButton(
                await tld(user_id, "SONG_BNT"),
                callback_data=f'_yta.{yt["id"]}|a|{user_id}|{user_id}|{key_search}|{scroll}'
            ),
            InlineKeyboardButton(
                await tld(user_id, "VID_BNT"),
                callback_data=f'_ytv.{yt["id"]}|v|{user_id}|{user_id}|{key_search}|{scroll}'
            ),
        ]
    ]

    
    if " - " in yt["title"]:
        performer, title = yt["title"].rsplit(" - ", 1)
    else:
        try:
            performer = yt.get("channel", {}).get("name", "N/A")
        except AttributeError:
            performer = None
        title = yt["title"]


    if scroll == True:
        # Save infos
        YT_VAR[key_search] = inf
        #Add a scroll buttons
        keyboard += [
            [
                InlineKeyboardButton(
                    f"1/{len(inf)}",
                    callback_data=f'yt_scroll|{key_search}|{user_id}|1|{user_id}'
                ),
            ],
        ]

    thumb_ = await get_ytthumb(yt["id"])

    text = f"🎧 <b>{performer}</b> - <i>{title}</i>\n\n"
    text += f"⏳ <code>{yt.get('duration', None)}</code>\n\n"
    text += f"🎥 <b> Views:</b> <code>{yt.get('viewCount', {}).get('short', 'N/A')}</code>\n\n"
    text += f"⏰ <code>{yt.get('publishedTime', None)}</code>"

    if found_:
        results.append(
            InlineQueryResultPhoto(
                photo_url=thumb_,
                thumb_url=iytdl_url_thumb,
                caption=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        )
    else:
        results.append(
                InlineQueryResultArticle(
                    title="not found",
                    input_message_content=InputTextMessageContent(
                        f"No result found for `{query}`"
                    ),
                    description="INVALID",
                )
            )
    await iq.answer(results=results, is_gallery=False, is_personal=True)
    iq.stop_propagation()

@WhiterX.on_callback_query(filters.regex(r"yt_scroll\|(.*)"))
async def scroll_ytdl(c: WhiterX, cq: CallbackQuery):
    try: 
        info = cq.data.split("|")
        key_search = info[1]
        user = int(info[2])
        pages = int(info[3])
        chat_id = int(info[4])
    except ValueError as vle:
        return await c.send_log(f"Scroll ValueError in: {cq.data} -> {vle}")
    
    chat_id = int(chat_id)
    
    if cq.from_user.id != user:
        return await cq.answer(await tld(chat_id, "NO_FOR_YOU"), show_alert=True)
    
    pages = int(pages)
    scroll = True

    infos = YT_VAR[key_search]
    l_infos = (len(infos))

    page = (pages+1)
    if page:
        if page == 1:
            if l_infos == 1:
                return await cq.answer("That's the end of list", show_alert=True)
        elif page >= l_infos:
            return await cq.answer("That's the end of list", show_alert=True)
    skip_page = (pages+5)
    back_page = (pages-1)

    yt = infos[page]
    yt_id = yt["id"]

    keyboard = [
        [
            InlineKeyboardButton(
                await tld(chat_id, "SONG_BNT"),
                callback_data=f'_yta.{yt_id}|a|{user}|{chat_id}|{key_search}|{scroll}'
            ),
            InlineKeyboardButton(
                await tld(chat_id, "VID_BNT"),
                callback_data=f'_ytv.{yt_id}|v|{user}|{chat_id}|{key_search}|{scroll}'
            ),
        ]
    ]

    
    if " - " in yt["title"]:
        performer, title = yt["title"].rsplit(" - ", 1)
    else:
        try:
            performer = yt.get("channel", {}).get("name", "N/A")
        except AttributeError:
            performer = None
        title = yt["title"]

    #Add a scroll buttons
    keyboard += [
        [
            InlineKeyboardButton(
                f"{page}/{l_infos}",
                callback_data=f'yt_scroll|{key_search}|{user}|{page}|{chat_id}'
            ),
        ],
    ]
    if page >= 2:
        keyboard += [
            [
                InlineKeyboardButton(
                    await tld(chat_id, "BACK_BNT"), 
                    callback_data=f"yt_scroll|{key_search}|{user}|{back_page}|{chat_id}"
                ),
                InlineKeyboardButton(
                    "⏭️ 5️",
                    callback_data=f"yt_scroll|{key_search}|{user}|{skip_page}|{chat_id}"
                ),
            ]
        ]

    thumb_ = await get_ytthumb(yt["id"])

    text = f"🎧 <b>{performer}</b> - <i>{title}</i>\n\n"
    text += f"⏳ <code>{yt.get('duration', None)}</code>\n\n"
    text += f"🎥 <b> Views:</b> <code>{yt.get('viewCount', {}).get('short', 'N/A')}</code>\n\n"
    text += f"⏰ <code>{yt.get('publishedTime', None)}</code>"

    await cq.edit_message_media(InputMediaPhoto(thumb_, caption=text), reply_markup=InlineKeyboardMarkup(keyboard))

@WhiterX.on_callback_query(filters.regex("^(_(ytv|yta))"))
async def cli_buttons(c: WhiterX, cq: CallbackQuery):
    try:
        yt_id, fmt, userid, chat_id, key_search, scroll = cq.data.split("|")
    except ValueError as vle:
        return print(f"{vle}: {cq.data}")
    
    chat_id = int(chat_id)

    if cq.from_user.id != int(userid):
        return await cq.answer(await tld(chat_id, "NO_FOR_YOU"), show_alert=True)
    
    yt_id = re.sub(r"^\_(ytv|yta)\.", "", yt_id)

    x = await get_download_button(fmt, yt_id, userid, chat_id, key_search, scroll)
    await cq.edit_message_caption(caption=x.caption, reply_markup=x.buttons)

@WhiterX.on_callback_query(filters.regex(r"yt_dl\|(.*)"))
async def download_handler(c: WhiterX, cq: CallbackQuery):
    try:
        data, yt_id, frmt_id, userid, type, chat_id = cq.data.split("|")
    except ValueError as vle:
        return print(f"{vle}: {cq.data}")
    
    chat_id = int(chat_id)

    if cq.from_user.id != int(userid):
        return await cq.answer(await tld(chat_id, "NO_FOR_YOU"), show_alert=True)

    if type == "a":
        format_ = "audio"
    else:
        format_ = "video"

    url = f"https://www.youtube.com/watch?v={yt_id}"

    if format_ == "video":
        await c.send_chat_action(chat_id, enums.ChatAction.RECORD_VIDEO)
    else:
        await c.send_chat_action(chat_id, enums.ChatAction.RECORD_AUDIO)

    try:
        await cq.edit_message_caption(caption=await tld(chat_id, "DOWNLOAD_YT"))
    except Exception as e:
        await c.send_err(e)

    with tempfile.TemporaryDirectory() as tempdir:
        path = os.path.join(tempdir, "ytdl")
    if format_ == "video":
        ydl = YoutubeDL(
            {
                "geo_bypass": True,
                "nocheckcertificate": True,
                "outtmpl": os.path.join(path, "%(title)s-%(format)s.%(ext)s"),
                "format": frmt_id,
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegMetadata"
                    },
                ]
            }
        )
    else:
        ydl = YoutubeDL(
            {
                "outtmpl": os.path.join(path, "%(title)s-%(format)s.%(ext)s"),
                "format": "bestaudio/best",
                "prefer_ffmpeg": True,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "postprocessors": [                    
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": frmt_id,
                    },
                ],
            }
        )

    try:
        yt = await extract_info(ydl, url, download=True)
    except BaseException as e:
        await c.send_log(e)
        try:
            await cq.edit_message_caption(caption="<b>Error:</b> <i>{}</i>".format(e))
        except Exception as err:
            return await c.send_err(err)
    try:
        await cq.edit_message_caption(await tld(chat_id, "UPLOADING_YT"))
    except Exception as uerr:
        return await c.send_err(uerr)

    if format_ == "video":
        await c.send_chat_action(chat_id, enums.ChatAction.UPLOAD_VIDEO)
    else:
        await c.send_chat_action(chat_id, enums.ChatAction.UPLOAD_AUDIO)

    filename = yt.get("requested_downloads")[0]["filepath"]

    thumb = io.BytesIO((await http.get(yt["thumbnail"])).content)
    thumb.name = "thumbnail.png"
    views = 0
    likes = 0
    if yt.get("view_count"):
        views += yt["view_count"]
    if yt.get("like_count"):
        likes += yt["like_count"]
    if format_ == "video":
        try:
            await cq.edit_message_media(
                media=InputMediaVideo(
                    media=filename, duration=yt["duration"], caption=(await tld(chat_id, "YOUTUBE_CAPTION")).format(url or "", yt["title"], datetime.timedelta(seconds=yt["duration"]) or 0, yt["channel"] or None, views, likes), thumb=thumb
                )
            )
        except BadRequest as e:
            await c.send_log(e)
            await c.send_message(
                chat_id=cq.message.chat.id,
                text="<b>Error:</b> {errmsg}".format(errmsg=e),
            )
    else:
        if " - " in yt["title"]:
            performer, title = yt["title"].rsplit(" - ", 1)
        else:
            performer = yt.get("creator") or yt.get("uploader")
            title = yt["title"]
        try:
            await cq.edit_message_media(
                media=InputMediaAudio(
                    media=filename, duration=yt["duration"], caption=(await tld(chat_id, "YOUTUBE_CAPTION")).format(url or "", yt["title"], datetime.timedelta(seconds=yt["duration"]) or 0, yt["channel"] or None, views, likes), thumb=thumb
                )
            )
        except BadRequest as e:
            try:
                await cq.message.edit_text(
                    "<b>Error:</b> <i>{errmsg}</i>".format(errmsg=e)
                )
            except Exception:
                await cq.edit_message_caption(caption="<b>Error:</b> <i>{errmsg}</i>".format(errmsg=e))

    shutil.rmtree(tempdir, ignore_errors=True)


@WhiterX.on_message(filters.command(["dl", "sdl", "mdl"], Config.TRIGGER) | filters.regex(SDL_REGEX_LINKS))
async def sdl(c: WhiterX, message: Message):
    if message.matches:
        if (
            message.chat.type is ChatType.PRIVATE
            or await csdl(message.chat.id)
        ):
            url = message.matches[0].group(0)
        else:
            return None
    elif not message.matches and len(message.command) > 1:
        url = message.text.split(None, 1)[1]
        if not re.match(SDL_REGEX_LINKS, url, re.M):
            return await message.reply_text("This link is not supported use Instagram Links, Tiktok Links, Threads Links, Twitter Links")
    elif message.reply_to_message and message.reply_to_message.text:
        url = message.reply_to_message.text
    else:
        return await message.reply_text(await tld(message.chat.id, "NO_ARGS_YT"))

    if message.chat.type == ChatType.PRIVATE:
        captions = await cisdl(message.from_user.id)
        method = messages.GetMessages(id=[InputMessageID(id=(message.id))])
    else:
        captions = await cisdl(message.chat.id)
        method = channels.GetMessages(
            channel=await c.resolve_peer(message.chat.id),
            id=[InputMessageID(id=(message.id))],
        )

    rawM = (await c.invoke(method)).messages[0].media
    try:
        files, caption = await DownloadMedia().download(url, captions)
    except BaseException as e:
        await asyncio.gather(c.send_err(f"[BaseException]: {e}"))
        return
    
    if len(caption) > 1024:
        caption = caption[:1019] + "(...)"
    
    medias = []
    for media in files:
        if filetype.is_video(media["p"]) and len(files) == 1:
            await c.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)
            return await message.reply_video(
                video=media["p"],
                width=media["h"],
                height=media["h"],
                caption=caption,
            )

        if filetype.is_video(media["p"]):
            if medias:
                medias.append(InputMediaVideo(media["p"], width=media["w"], height=media["h"]))
            else:
                medias.append(
                    InputMediaVideo(
                        media["p"],
                        width=media["w"],
                        height=media["h"],
                        caption=caption,
                    )
                )
        elif not medias:
            medias.append(InputMediaPhoto(media["p"], caption=caption))
        else:
            medias.append(InputMediaPhoto(media["p"]))

    if medias:
        if (
            rawM
            and not re.search(r"(instagram.com/|threads.net)", url)
            and len(medias) == 1
            and "InputMediaPhoto" in str(medias[0])
        ):
            return None

        await c.send_chat_action(message.chat.id, ChatAction.UPLOAD_DOCUMENT)
        await message.reply_media_group(media=medias)
        return None
    return None


@WhiterX.on_callback_query(filters.regex(r"^media_config"))
@require_admin(ChatPrivileges(can_change_info=True), allow_in_private=True)
async def media_config(c: WhiterX, callback: CallbackQuery):
    chat = callback.message.chat

    state = ["☑️", "✅"]
    
    if "+" in callback.data and not (await cisdl(chat.id)):
        await tisdl(chat.id, True)
    elif "+" in callback.data and (await cisdl(chat.id)):
        await tisdl(chat.id, False)

    keyboard = [
        [
            InlineKeyboardButton(await tld(chat.id, "MEDIAS_CAPTION_BNT"), "media_config"),
            InlineKeyboardButton(state[(await cisdl(chat.id))], "media_config+"),
        ],
    ]

    if chat.type != ChatType.PRIVATE:
        if "-" in callback.data and not (await csdl(chat.id)):
            await tsdl(chat.id, True)
        elif "-" in callback.data and (await csdl(chat.id)):
            await tsdl(chat.id, False)

        keyboard += [
            [
                    InlineKeyboardButton(await tld(chat.id, "AUTO_DOWNLOAD_BNT"), "media_config"),
                    InlineKeyboardButton(state[(await csdl(chat.id))], "media_config-"),
            ]
        ]

    keyboard += [[InlineKeyboardButton(await tld(chat.id, "BACK_BNT"), "config")]]
    return await callback.edit_message_text(
        await tld(chat.id, "MEDIAS_CONFIG_TEXT"), reply_markup=InlineKeyboardMarkup(keyboard)
    )

@WhiterX.on_callback_query(filters.regex(r"config"))
@WhiterX.on_message(filters.command("config", Config.TRIGGER))
@require_admin(ChatPrivileges(can_change_info=True))
async def config(c: WhiterX, union: Message | CallbackQuery):
    reply = union.edit_message_text if isinstance(union, CallbackQuery) else union.reply_text
    chat = union.message.chat if isinstance(union, CallbackQuery) else union.chat

    keyboard = [
        [
            InlineKeyboardButton(await tld(chat.id, "MEDIAS_BNT"), "media_config"),
        ],
        [
            InlineKeyboardButton(await tld(chat.id, "button_lang"), "lang_menu"),
        ],
    ]

    await reply(await tld(chat.id, "CONFIG_TEXT"), reply_markup=InlineKeyboardMarkup(keyboard))

@WhiterX.on_message(filters.command("yt", Config.TRIGGER))
async def yt_search_cmd(c: WhiterX, m: Message):
    vids = [
        '{}: <a href="{}">{}</a>'.format(num + 1, i["url"], i["title"])
        for num, i in enumerate(await search_yt(m.text.split(None, 1)[1]))
    ]
    await m.reply_text(
        "\n".join(vids) if vids else r"¯\_(ツ)_/¯", disable_web_page_preview=True
    )

inline_handler.add_cmd("iytdl <query>", "A advanced downloader from medias of the YouTube.", iytdl_url_thumb, aliases=["iytdl", "ytdl"])

__help__ = True