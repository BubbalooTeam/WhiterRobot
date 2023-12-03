import asyncio
import os

from wget import download
from bs4 import BeautifulSoup as bs
from telegraph import upload_file

from hydrogram import filters
from hydrogram.enums import ChatType
from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultPhoto

from whiterkang import WhiterX, Config, db
from whiterkang.helpers import disableable_dec, http, add_gp, find_user, add_user, find_gp, search_yt, draw_scrobble, tld, input_str, inline_handler

API = "http://ws.audioscrobbler.com/2.0"
LAST_KEY = Config.LASTFM_API_KEY
REG = db["USERS"]

@WhiterX.on_message(filters.command(["setuser", "reg", "set"], Config.TRIGGER))
@disableable_dec("set")
async def last_save_user(c: WhiterX, m: Message):
    user_id = m.from_user.id
    fname = m.from_user.first_name
    uname = m.from_user.username
    text = input_str(m)
    if not text:
        await m.reply(await tld(m.chat.id, "NO_SET_USERNAME_LAST"))
        return
    found = await REG.find_one({"id_": user_id})
    user_start = f"#USER_REGISTER #LOGS\n\n<b>User:</b> {fname}\n<b>ID:</b> {user_id} <a href='tg://user?id={user_id}'><b>Link</b></a>"
    if uname:
        user_start += f"\n<b>Username:</b> @{uname}"
    if found:
        await asyncio.gather(
                REG.update_one({"id_": user_id}, {
                                "$set": {"last_data": text}}, upsert=True),
                m.reply(await tld(m.chat.id, "UPDATE_USER_LAST"))
            )
    else:
        await asyncio.gather(
                REG.update_one({"id_": user_id}, {
                                "$set": {"last_data": text}}, upsert=True),
                c.send_log(
                    user_start,
                    disable_notification=False,
                    disable_web_page_preview=True,
                ),
                m.reply(await tld(m.chat.id, "SET_USER_LAST"))
            )

@WhiterX.on_message(filters.command(["deluser", "duser"], Config.TRIGGER))
@disableable_dec("deluser")
async def last_del_user(c: WhiterX, m: Message):
    user_id = m.from_user.id
    found = await REG.find_one({"id_": user_id})
    if found:
        await asyncio.gather(
                REG.delete_one(found),
                m.reply(await tld(m.chat.id, "USER_DELETED"))
            )
    else:
        return await m.reply(await tld(m.chat.id, "NO_USER_DELETE"))

@WhiterX.on_message(filters.command(["profile", "user"], Config.TRIGGER))
@disableable_dec("profile")
async def profile(c: WhiterX, m: Message):
    user_ = m.from_user
    lastdb = await REG.find_one({"id_": user_.id})
    if not lastdb:
        button = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        await tld(m.chat.id, "LAST_CREATE_ACCOUNT_BNT"), url="https://www.last.fm/join"
                    )
                ]
            ]
        )
        reg_ = await tld(m.chat.id, "CREATE_LASTFM_ACCOUNT")
        await m.reply(reg_, reply_markup=button)
        return
    user_lastfm = lastdb["last_data"]
    params = {
        "method": "user.getinfo",
        "user": user_lastfm,
        "api_key": Config.LASTFM_API_KEY,
        "format": "json",
    }
    try:
        view_data_ = await http.get(API, params=params)
        view_data = view_data_.json()
    except ValueError:
        return await m.reply(await tld(m.chat.id, "ERROR_LASTFM_USERNAME"))
    params_ = {
        "method": "user.getrecenttracks",
        "user": user_lastfm,
        "api_key": Config.LASTFM_API_KEY,
        "limit": 3,
        "format": "json",
    }
    try:
        view_scr_ = await http.get(API, params=params_)
        view_scr = view_scr_.json()
    except ValueError:
        return await m.reply(await tld(m.chat.id, "ERROR_LASTFM_USERNAME"))

    # == scrap site
    url_ = f"https://www.last.fm/user/{user_lastfm}/loved"
    get_url_ = await http.get(url_)
    get_url = get_url_.text
    soup = bs(get_url, "html.parser")
    try:
        scrob = soup.select('h1.content-top-header')[0].text.strip()
        scrr = scrob.split()[2].replace("(", "").replace(")", "")
    except IndexError:
        scrr = None
    
    # == user latest scrobbles
    scr_ = view_scr["recenttracks"]["track"]
    kek = ""
    for c in scr_:
        kek += f"    ♪ <b>{c['name']}</b> - <i>{c['artist']['#text']}</i>\n"

    # == user data
    data = view_data["user"]
    usuario = data["name"]
    user_url = data["url"]
    playcount = data["playcount"]
    country = data["country"]
    userr = f"<a href='{user_url}'>{usuario}</a>"
    text_ = (await tld(m.chat.id, "PROFILE_USER")).format(userr)
    if playcount:
        text_ += (await tld(m.chat.id, "PROFILE_SCROBBLES")).format(playcount)
    if country:
        text_ += (await tld(m.chat.id, "PROFILE_COUNTRY")).format(country)
    if scrr:
        text_ += (await tld(m.chat.id, "PROFILE_LOVED")).format(scrr)
    if scr_:
        text_ += (await tld(m.chat.id, "PROFILE_LATEST")).format(kek)
    await m.reply(text_, disable_web_page_preview=True)

@WhiterX.on_message(filters.command("status", prefixes=""))
@WhiterX.on_message(filters.command(["lt", "lastfm", "lmu"], Config.TRIGGER))
@disableable_dec("lt")
async def now_play(c: WhiterX, m: Message):
    if m.chat.type == (ChatType.SUPERGROUP or ChatType.GROUP):
        if not await find_gp(m.chat.id):
            await add_gp(m)
    user = m.from_user
    find_username = await REG.find_one({"id_": user.id})
    if not find_username:
        await add_user(user.id)
        await asyncio.sleep(1)
        button = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        await tld(m.chat.id, "LAST_CREATE_ACCOUNT_BNT"), url="https://www.last.fm/join"
                    )
                ]
            ]
        )
        await m.reply(await tld(m.chat.id, "CREATE_LASTFM_ACCOUNT"), reply_markup=button)
        return
    try:
        user_lastfm_ = await REG.find_one({"id_": user.id})
        user_lastfm = user_lastfm_["last_data"]
    except Exception:
        user_lastfm_ = None
        user_lastfm = None

    # request on lastfm
    params = {
        "method": "user.getrecenttracks",
        "limit": 1,
        "extended": 1,
        "user": user_lastfm,
        "api_key": Config.LASTFM_API_KEY,
        "limit": 1,
        "format": "json",
    }
    try:
        view_data_ = await http.get(API, params=params)
        view_data = view_data_.json()
    except ValueError:
        return await m.reply(await tld(m.chat.id, "ERROR_LASTFM_USERNAME"))
    recent_song = view_data["recenttracks"]["track"]
    if len(recent_song) == 0:
        return await m.reply(await tld(m.chat.id, "NONE_MUSIC_SCROBBLE"))
    song_ = recent_song[0]
    song_name = song_["name"]
    artist_name = song_["artist"]["name"]
    image_ = song_["image"][3].get("#text")
    params_ = {
        "method": "track.getInfo",
        "track": song_name,
        "artist": artist_name,
        "user": user_lastfm,
        "api_key": Config.LASTFM_API_KEY,
        "format": "json",
    }
    try:
        view_data_ = await http.get(API, params=params_)
        view_data = view_data_.json()
        get_track = view_data["track"]
        get_scrob = int(get_track["userplaycount"])
        if get_scrob == 0:
            scrob = get_scrob + 1
        else:
            scrob = get_scrob
        listening = (await tld(m.chat.id, "IS_LISTERING_")).format(scrob)
    except KeyError:
        listening = await tld(m.chat.id, "IS_LISTERING")
    if image_:
        img_ = download(image_, Config.DOWN_PATH)
    else:
        img_ = download(
            "https://telegra.ph/file/bdcf492162713ea5633a1.jpg", Config.DOWN_PATH)
    loved = int(song_["loved"])

    # User Photo
    if user.photo:
        photos = m.from_user.photo.big_file_id
        pfp = await WhiterX.download_media(photos)
    else:
        pfp = 'whiterkang/resources/user.png'

    image = draw_scrobble(img_, pfp, song_name, artist_name,
                          user_lastfm, listening, loved)
    prof = f"https://www.last.fm/user/{user_lastfm}"

    pre_link_ = f"{song_name} {artist_name}"
    pre_link_ = await search_yt(pre_link_)
    link_ = pre_link_[0]["url"]

    button_ = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    await tld(m.chat.id, "LAST_YOUTUBE_BNT"), url=link_
                ),
                InlineKeyboardButton(
                    await tld(m.chat.id, "LAST_PROFILE_BNT"), url=prof
                ),
                InlineKeyboardButton(
                    await tld(m.chat.id, "LAST_SHARE_BNT"), switch_inline_query="status"
                ),
            ]
        ]
    )
    # send pic
    await m.reply_photo(image, reply_markup=button_)
    try:
        os.remove(img_)
        os.remove(pfp)
        os.system("rm *.jpg")
    except FileNotFoundError:
        pass


@WhiterX.on_inline_query(filters.regex(r"^status"))
async def now_play(c: WhiterX, cb: InlineQuery):
    results = []
    user = cb.from_user
    find_username = await REG.find_one({"id_": user.id})
    if find_username:
        user_lastfm = find_username["last_data"]
        params = {
            "method": "user.getrecenttracks",
            "limit": 1,
            "extended": 1,
            "user": user_lastfm,
            "api_key": Config.LASTFM_API_KEY,
            "limit": 1,
            "format": "json",
        }
        try:
            view_data_ = await http.get(API, params=params)
            view_data = view_data_.json()
        except ValueError:
            results.append(
                InlineQueryResultArticle(
                    title=await tld(cb.from_user.id, "ERROR_LASTFM_USERNAME"),
                    thumb_url="https://telegra.ph/file/bdcf492162713ea5633a1.jpg",
                )
            )
            return await cb.answer(
                results=results,
                cache_time=1
            )
        if "error" in view_data:
            results.append(
                InlineQueryResultArticle(
                    title=await tld(cb.from_user.id, "ERROR_LASTFM_USERNAME"),
                    thumb_url="https://telegra.ph/file/bdcf492162713ea5633a1.jpg",
                )
            )
            return await cb.answer(
                results=results,
                cache_time=1
            )
        recent_song = view_data["recenttracks"]["track"]
        if len(recent_song) == 0:
            results.append(
                InlineQueryResultArticle(
                    title=await tld(cb.from_user.id, "NONE_MUSIC_SCROBBLE"),
                    thumb_url="https://telegra.ph/file/bdcf492162713ea5633a1.jpg",
                )
            )
            return await cb.answer(
                results=results,
                cache_time=1
            )
        song_ = recent_song[0]
        song_name = song_["name"]
        artist_name = song_["artist"]["name"]
        image_ = song_["image"][3]["#text"]
        params_ = {
            "method": "track.getInfo",
            "track": song_name,
            "artist": artist_name,
            "user": user_lastfm,
            "api_key": Config.LASTFM_API_KEY,
            "format": "json",
        }
        try:
            view_data_ = await http.get(API, params=params_)
            view_data = view_data_.json()
            get_track = view_data["track"]
            get_scrob = int(get_track["userplaycount"])
            if get_scrob == 0:
                scrob = get_scrob + 1
            else:
                scrob = get_scrob
            listening = (await tld(cb.from_user.id, "IS_LISTERING_")).format(scrob)
        except KeyError:
            listening = await tld(cb.from_user.id, "IS_LISTERING")
        if image_:
            img_ = download(image_)
        else:
            img_ = download(
                "https://telegra.ph/file/bdcf492162713ea5633a1.jpg")
        loved = int(song_["loved"])

        # User Photo
        if user.photo:
            photos = cb.from_user.photo.big_file_id
            pfp = await WhiterX.download_media(photos)
        else:
            pfp = 'whiterkang/resources/user.png'

        image = draw_scrobble(img_, pfp, song_name,
                              artist_name, user_lastfm, listening, loved)
        response = upload_file(image)
        inquery = f"https://telegra.ph{response[0]}"
        await asyncio.sleep(0.5)
        prof = f"https://www.last.fm/user/{user_lastfm}"

        pre_link_ = f"{song_name} {artist_name}"
        pre_link_ = await search_yt(pre_link_)
        link_ = pre_link_[0]["url"]

        button_ = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        await tld(cb.from_user.id, "LAST_YOUTUBE_BNT"), url=link_
                    ),
                    InlineKeyboardButton(
                        await tld(cb.from_user.id, "LAST_PROFILE_BNT"), url=prof
                    ),
                    InlineKeyboardButton(
                        await tld(cb.from_user.id, "LAST_SHARE_BNT"), switch_inline_query="status"
                    ),
                ]
            ]
        )
        # send pic
        results.append(
            InlineQueryResultPhoto(
                title=listening,
                thumb_url=inquery,
                photo_url=inquery,
                description=await tld(cb.from_user.id, "IS_LISTERING"),
                reply_markup=button_
            )
        )
        await cb.answer(
            results=results,
            cache_time=0,
        )
        try:
            os.remove(img_)
            os.remove(pfp)
            os.system("rm *.jpg")
        except FileNotFoundError:
            pass
    else:
        reg_ = await tld(cb.from_user.id, "UNREGISTRED_USER_PM")
        button = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        await tld(cb.from_user.id, "LAST_GO_PM"), url=f"https://t.me/{c.me.username}"
                    )
                ]
            ]
        )
        results.append(
            InlineQueryResultArticle(
                title=await tld(cb.from_user.id, "UNREGISTRED_USER"),
                input_message_content=InputTextMessageContent(reg_),
                thumb_url="https://telegra.ph/file/21581612f3170612568dd.jpg",
                reply_markup=button
            )
        )
        await cb.answer(
            results=results,
            cache_time=1
        )

inline_handler.add_cmd("status", "Share the music you are listening to with your friends.", "https://telegra.ph/file/d9e8a2572131b2f5205ae.jpg", aliases=["lastfm", "lt"])