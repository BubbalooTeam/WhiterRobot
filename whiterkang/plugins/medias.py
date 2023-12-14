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
from bs4 import BeautifulSoup

from hydrogram import filters, enums
from hydrogram.errors import BadRequest, FloodWait, Forbidden, MediaEmpty, MessageNotModified, UserNotParticipant
from hydrogram.raw.types import InputMessageID
from hydrogram.raw.functions import channels, messages
from hydrogram.types import Message, CallbackQuery, InputMediaVideo, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton, ChatPrivileges
from hydrogram.enums import ChatType, ChatAction 


from whiterkang import WhiterX, Config 
from whiterkang.helpers import humanbytes, tld, csdl, cisdl, tsdl, tisdl, DownloadMedia, extract_info, http, is_admin, add_user, find_user, search_yt, require_admin, disableable_dec, get_ytthumb, rand_key, get_download_button, SearchResult


YOUTUBE_REGEX = re.compile(
    r"(?m)http(?:s?):\/\/(?:www\.)?(?:music\.)?youtu(?:be\.com\/(watch\?v=|shorts/|embed/)|\.be\/|)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?"
)

SDL_REGEX_LINKS = r"(?:htt.+?//)?(?:.+?)?(?:instagram|twitter|x|tiktok|threads).(com|net)\/(?:\S*)"

TIME_REGEX = re.compile(r"[?&]t=([0-9]+)")

MAX_FILESIZE = 2000000000

YT_VAR = {}

@WhiterX.on_message(filters.command("ytdl", Config.TRIGGER))
@disableable_dec("ytdl")
async def ytdlcmd(c: WhiterX, m: Message):
    user = m.from_user.id
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

    t = TIME_REGEX.search(url)
    temp = t.group(1) if t else 0

    if not rege:
        yt = await extract_info(ydl, f"ytsearch:{url}", download=False)
        scroll = True
        try:
            yt = yt["entries"][0]
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
                callback_data=f'_yta.{yt["id"]}|{key_search}|{temp}|{user}'
            ),
            InlineKeyboardButton(
                await tld(m.chat.id, "VID_BNT"),
                callback_data=f'_ytv.{yt["id"]}|{key_search}|{temp}|{user}'
            ),
        ]
    ]

    
    if " - " in yt["title"]:
        performer, title = yt["title"].rsplit(" - ", 1)
    else:
        performer = yt.get("creator") or yt.get("uploader")
        title = yt["title"]


    if scroll == True:
        #Getting infos
        inf = await search_yt(url)
        # Save infos
        YT_VAR[key_search] = inf
        #Add a scroll buttons
        keyboard += [
            [
                InlineKeyboardButton(
                    f"1/{len(inf)}",
                    callback_data=f'yt_scroll.{key_search}|{user}|1'
                ),
            ],
        ]

    thumb_ = await get_ytthumb(yt["id"])

    text = f"🎧 <b>{performer}</b> - <i>{title}</i>\n"
    text += f"⏳ <code>{datetime.timedelta(seconds=yt.get('duration'))}</code>"

    await m.reply_photo(photo=thumb_, caption=text, reply_markup=InlineKeyboardMarkup(keyboard))

@WhiterX.on_callback_query(filters.regex("^yt_scroll\.\w{8}\|\d+\|[0-9]{1,3}$"))
async def scroll_ytdl(c: WhiterX, cq: CallbackQuery):
    try:
        key_search, user, pages = cq.data.split("|")
    except ValueError:
        return await c.send_log("Scroll ValueError in: {cq.data}")
    
    chat = cq.message.chat
    
    if cq.from_user.id != int(user):
        return await cq.answer(await tld(chat.id, "NO_FOR_YOU"), show_alert=True)
    
    ydl = YoutubeDL({"noplaylist": True})

    key_search = re.sub(r"^yt_scroll\.", "", key_search)
    pages = int(pages)

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
    print(key_search)
    print(page)
    url = infos[page]["url"]
    rege = YOUTUBE_REGEX.match(url)

    t = TIME_REGEX.search(url)
    temp = t.group(1) if t else 0

    yt = await extract_info(ydl, rege.group(), download=False)

    keyboard = [
        [
            InlineKeyboardButton(
                await tld(chat.id, "SONG_BNT"),
                callback_data=f'_yta.{yt["id"]}|{key_search}|{temp}|{user}'
            ),
            InlineKeyboardButton(
                await tld(chat.id, "VID_BNT"),
                callback_data=f'_vid.{yt["id"]}|{key_search}|{temp}|{user}'
            ),
        ]
    ]

    
    if " - " in yt["title"]:
        performer, title = yt["title"].rsplit(" - ", 1)
    else:
        performer = yt.get("creator") or yt.get("uploader")
        title = yt["title"]

    #Add a scroll buttons
    keyboard += [
        [
            InlineKeyboardButton(
                f"{page}/{l_infos}",
                callback_data=f'yt_scroll.{key_search}|{user}|{page}'
            ),
        ],
    ]
    if page >= 2:
        keyboard += [
            [
                InlineKeyboardButton(
                    await tld(chat.id, "BACK_BNT"), 
                    callback_data=f"yt_scroll.{key_search}|{user}|{back_page}"
                ),
                InlineKeyboardButton(
                    "⏭️ 5️",
                    callback_data=f"yt_scroll.{key_search}|{user}|{skip_page}"
                ),
            ]
        ]

    thumb_ = await get_ytthumb(yt["id"])

    text = f"🎧 <b>{performer}</b> - <i>{title}</i>\n"
    text += f"⏳ <code>{datetime.timedelta(seconds=yt.get('duration'))}</code>"

    await cq.edit_message_media(InputMediaPhoto(thumb_, caption=text), reply_markup=InlineKeyboardMarkup(keyboard))

@WhiterX.on_callback_query(filters.regex("^(_(ytv|yta))"))
async def cli_buttons(c: WhiterX, cq: CallbackQuery):
    try:
        yt_id, key_search, temp, userid = cq.data.split("|")
    except ValueError as vle:
        return print(f"{vle}: {cq.data}")
    if cq.from_user.id != int(userid):
        return await cq.answer(await tld(cq.message.chat.id, "NO_FOR_YOU"), show_alert=True)
    
    yt_id = re.sub("^(_(ytv|yta))", "", yt_id)

    x = await get_download_button(yt_id, userid)
    await cq.edit_message_caption(caption=temp + x.caption, reply_markup=x.buttons)

@WhiterX.on_callback_query(filters.regex(r"yt_dl\|(.*)"))
async def download_handler(c: WhiterX, cq: CallbackQuery):
    try:
        data, yt_id, frmt_id, userid, type = cq.data.split("|")
    except ValueError:
        return print(cq.data)
    if cq.from_user.id != int(userid):
        return await cq.answer(await tld(cq.message.chat.id, "NO_FOR_YOU"), show_alert=True)
    
    if type == "a":
        format_ = "audio"
    else:
        format_ = "video"

    url = f"https://www.youtube.com/watch?v={yt_id}"

    try:
        await cq.message.edit(await tld(cq.message.chat.id, "DOWNLOAD_YT"))
    except MessageNotModified:
        await cq.message.reply_text(await tld(cq.message.chat.id, "DOWNLOAD_YT"))

    with tempfile.TemporaryDirectory() as tempdir:
        path = os.path.join(tempdir, "ytdl")
    if format_ == "video":
        ydl = {
            "addmetadata": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "outtmpl": os.path.join(path, "%(title)s-%(format)s.%(ext)s"),
            "format": frmt_id,
            "writethumbnail": True,
            "prefer_ffmpeg": True,
            "postprocessors": [{"key": "FFmpegMetadata"}],
        }
    else:
        ydl = {
            "outtmpl": os.path.join(path, "%(title)s-%(format)s.%(ext)s"),
            "writethumbnail": True,
            "prefer_ffmpeg": True,
            "format": "bestaudio/best",
            "geo_bypass": True,
            "nocheckcertificate": True,
            "postprocessors": [                    {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": frmt_id,
                },
                {"key": "EmbedThumbnail"},
                {"key": "FFmpegMetadata"},
            ],
        }

    try:
        yt = await extract_info(ydl, url, download=True)
    except BaseException as e:
        await c.send_log(e)
        await cq.message.edit("<b>Error:</b> <i>{}</i>".format(e))
        return
    try:
        await cq.message.edit(await tld(cq.message.chat.id, "UPLOADING_YT"))
    except MessageNotModified:
        await cq.message.reply_text(await tld(cq.message.chat.id, "UPLOADING_YT"))
    await c.send_chat_action(cq.message.chat.id, enums.ChatAction.UPLOAD_VIDEO)

    filename = ydl.prepare_filename(yt)
    thumb = io.BytesIO((await http.get(yt["thumbnail"])).content)
    thumb.name = "thumbnail.png"
    views = 0
    likes = 0
    if yt.get("view_count"):
        views += yt["view_count"]
    if yt.get("like_count"):
        likes += yt["like_count"]
    if "vid" in data:
        try:
            await c.send_video(
                cq.message.chat.id,
                video=filename,
                width=1920,
                height=1080,
                caption=(await tld(cq.message.chat.id, "YOUTUBE_CAPTION")).format(url or "",  + yt["title"], datetime.timedelta(seconds=yt["duration"]) or 0, yt["channel"] or None, views, likes),
                duration=yt["duration"],
                thumb=thumb,
            )
            await cq.message.delete()
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
            await c.send_audio(
                cq.message.chat.id,
                audio=filename,
                title=title,
                performer=performer,
                caption=(await tld(cq.message.chat.id, "YOUTUBE_CAPTION")).format(url or "", yt["title"], datetime.timedelta(seconds=yt["duration"]) or 0, yt["channel"] or None, views, likes),
                duration=yt["duration"],
                thumb=thumb,
            )
        except BadRequest as e:
            await cq.message.edit_text(
                "<b>Error:</b> <i>{errmsg}</i>".format(errmsg=e)
            )
        else:
            await cq.message.delete()

    shutil.rmtree(tempdir, ignore_errors=True)


    

@WhiterX.on_callback_query(filters.regex("^(_(vid|aud))"))
async def cli_ytdl(c: WhiterX, cq: CallbackQuery):
    try:
        data, fsize, vformat, temp, userid, mid = cq.data.split("|")
    except ValueError:
        return print(cq.data)
    if cq.from_user.id != int(userid):
        return await cq.answer(await tld(cq.message.chat.id, "NO_FOR_YOU"), show_alert=True)
    if int(fsize) > MAX_FILESIZE:
        return await cq.answer(
            await tld(cq.message.chat.id, "YOUTUBE_FILE_BIG"),
            show_alert=True,
            cache_time=60,
        )
    vid = re.sub(r"^\_(vid|aud)\.", "", data)
    url = f"https://www.youtube.com/watch?v={vid}"
    try:
        await cq.message.edit(await tld(cq.message.chat.id, "DOWNLOAD_YT"))
    except MessageNotModified:
        await cq.message.reply_text(await tld(cq.message.chat.id, "DOWNLOAD_YT"))
    with tempfile.TemporaryDirectory() as tempdir:
        path = os.path.join(tempdir, "ytdl")

    ttemp = f"⏰ {datetime.timedelta(seconds=int(temp))} | " if int(temp) else ""
    if "vid" in data:
        ydl = YoutubeDL(
            {
                "outtmpl": f"{path}/%(title)s-%(id)s.%(ext)s",
                "format": f"{vformat}+140",
                "max_filesize": MAX_FILESIZE,
                "noplaylist": True,
            }
        )
    else:
        ydl = YoutubeDL(
            {
                "outtmpl": f"{path}/%(title)s-%(id)s.%(ext)s",
                "format": "bestaudio[ext=m4a]",
                "max_filesize": MAX_FILESIZE,
                "noplaylist": True,
            }
        )
    try:
        yt = await extract_info(ydl, url, download=True)
    except BaseException as e:
        await c.send_log(e)
        await cq.message.edit("<b>Error:</b> <i>{}</i>".format(e))
        return
    try:
        await cq.message.edit(await tld(cq.message.chat.id, "UPLOADING_YT"))
    except MessageNotModified:
        await cq.message.reply_text(await tld(cq.message.chat.id, "UPLOADING_YT"))
    await c.send_chat_action(cq.message.chat.id, enums.ChatAction.UPLOAD_VIDEO)

    filename = ydl.prepare_filename(yt)
    thumb = io.BytesIO((await http.get(yt["thumbnail"])).content)
    thumb.name = "thumbnail.png"
    views = 0
    likes = 0
    if yt.get("view_count"):
        views += yt["view_count"]
    if yt.get("like_count"):
        likes += yt["like_count"]
    if "vid" in data:
        try:
            await c.send_video(
                cq.message.chat.id,
                video=filename,
                width=1920,
                height=1080,
                caption=(await tld(cq.message.chat.id, "YOUTUBE_CAPTION")).format(url or "", ttemp + yt["title"], datetime.timedelta(seconds=yt["duration"]) or 0, yt["channel"] or None, views, likes),
                duration=yt["duration"],
                thumb=thumb,
                reply_to_message_id=int(mid),
            )
            await cq.message.delete()
        except BadRequest as e:
            await c.send_log(e)
            await c.send_message(
                chat_id=cq.message.chat.id,
                text="<b>Error:</b> {errmsg}".format(errmsg=e),
                reply_to_message_id=int(mid),
            )
    else:
        if " - " in yt["title"]:
            performer, title = yt["title"].rsplit(" - ", 1)
        else:
            performer = yt.get("creator") or yt.get("uploader")
            title = yt["title"]
        try:
            await c.send_audio(
                cq.message.chat.id,
                audio=filename,
                title=title,
                performer=performer,
                caption=(await tld(cq.message.chat.id, "YOUTUBE_CAPTION")).format(url or "", ttemp + yt["title"], datetime.timedelta(seconds=yt["duration"]) or 0, yt["channel"] or None, views, likes),
                duration=yt["duration"],
                thumb=thumb,
                reply_to_message_id=int(mid),
            )
        except BadRequest as e:
            await cq.message.edit_text(
                "<b>Error:</b> <i>{errmsg}</i>".format(errmsg=e)
            )
        else:
            await cq.message.delete()

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

__help__ = True