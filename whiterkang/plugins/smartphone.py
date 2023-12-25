# Copyright (C) 2023 BubbalooTeam
import bs4
import requests
import rapidjson
import re
import asyncio

from bs4 import BeautifulSoup
from babel.dates import format_datetime
from yaml import load, Loader

from hydrogram import filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from whiterkang import WhiterX, Config, db
from whiterkang.helpers import disableable_dec, is_disabled, search_device, get_device, add_user, find_user, tld, gsmarena_tr_category, gsmarena_tr_info, input_str, humanbytes, http, add_device, find_device, del_device
CATEGORY_EMOJIS = {
    "Display": "📱",
    "Platform": "⚙️",
    "Memory": "💾",
    "Main Camera": "📷",
    "Selfie camera": "🤳",
    "Sound": "🔈",
    "Network": "🌐",
    "Battery": "🔋",
    "Body": "🏗",
    "Launch": "🚀",
    "Comms": "📡",
    "Features": "✨",
    "Misc": "📦",
    "Tests": "ℹ️"
}

DEVICE_LIST = "https://raw.githubusercontent.com/androidtrackers/certified-android-devices/master/by_device.json"

DB_DEVICES = db["DEVICES"]

@WhiterX.on_message(filters.command(["deviceinfo", "d"], Config.TRIGGER))
@disableable_dec("deviceinfo")
async def deviceinfo(c: WhiterX, m: Message):
    if not await find_user(m.from_user.id):
        await add_user(m.from_user.id)

    getlist = requests.get(DEVICE_LIST).json()

    if input_str(m):
        name = input_str(m).lower()
        if name in list(getlist):
            searchi = getlist.get(name)[0]['name'].replace(" ", "+")
        else:
            searchi = f"{name}".replace(" ", "+")
            
        get_search_api = await search_device(searchi)
        
        if not get_search_api == []:
            if len(get_search_api) == 1:
                name = get_search_api[0]["name"]
                img = get_search_api[0]["img"]
                id = get_search_api[0]["id"]
                link = f"https://www.gsmarena.com/{id}.php"
                description = get_search_api[0]["description"]
            
                try:
                    get_device_api = await get_device(id)
                    name_cll = get_device_api.get("name", "N/A")
                    base_device = f"<b>Photo Device:</b> <i>{img}</i>\n<b>Source URL:</b> <i>{link}</i>"
                    DEVICE_TEXT = f"{base_device}\n\n📌 <b><u>{name_cll}</b></u>\n📅 <b>Announced:</b> <i>{get_device_api['detailSpec'][1]['specifications'][0]['value']}</i>"
                
                    for spec_index in range(14):
                        try:
                            base_category = get_device_api['detailSpec'][spec_index]['category']
                            translated_category = CATEGORY_EMOJIS.get(base_category, '')
                            category = gsmarena_tr_category(base_category, await tld(m.chat.id, "language"))
                            specs = get_device_api['detailSpec'][spec_index]['specifications']
                            section_text = f"\n\n<b>{translated_category} <u>{category}</b></u>:\n"
                        
                            for spec in specs:
                                base_name = spec['name']
                                name = gsmarena_tr_info(base_name, await tld(m.chat.id, "language"))
                                value = spec['value']
                                section_text += f"- <b>{name}:</b> <i>{value}</i>\n\n"
                        
                            DEVICE_TEXT += section_text
                        except (IndexError, KeyError):
                            pass
                        
                    #Create Description
                    DEVICE_TEXT += f"\n\n<b>Description</b>: <i>{description}</i>"
                
                    try:
                        await m.reply(DEVICE_TEXT, disable_web_page_preview=False)
                    except Exception as err:
                        # Send the image with the first part of the caption
                        caption_part = DEVICE_TEXT[:1024]
                        caption_rest = DEVICE_TEXT[1024:]

                        await c.send_photo(chat_id=m.chat.id, photo=img, caption=caption_part)

                        # Split the remaining caption and send as regular text messages
                        message_chunks = [caption_rest[i:i + 4096] for i in range(0, len(caption_rest), 4096)]
                        for chunk in message_chunks:
                            await c.send_message(chat_id=m.chat.id, text=chunk)
                    
                    
                except Exception as err:
                    return await m.reply(f"Couldn't retrieve device details. The GSM Arena website might be offline. <i>Error</i>: <b>{err}</b>\n<b>Line</b>: {err.__traceback__.tb_lineno}")
            else:
                buttons = []
                user_id = m.from_user.id
                try:
                    for devices in get_search_api:
                        device_id = devices["id"]
                        img = devices["img"]
                        link = f"https://www.gsmarena.com/{device_id}.php"
                        description = devices["description"]
                        device_geral = await get_device(device_id)
                        device_name = device_geral.get("name", "N/A")
                        await add_device(user_id, device_id, link, img, description)
                        buttons.append([InlineKeyboardButton(device_name, callback_data=f"d.{device_id}|{user_id}")])
                        if len(buttons) >= 30:
                            break

                    reply_markup = InlineKeyboardMarkup(buttons)
                    await m.reply("Por favor, escolha um dispositivo:", reply_markup=reply_markup)
                except Exception as err:
                    return await m.reply(f"Couldn't retrieve device details. The GSM Arena website might be offline. <i>Error</i>: <b>{err}</b>\n<b>Line</b>: {err.__traceback__.tb_lineno}")

        else:
            return await m.reply("Couldn't find this device! :(")
    else:
        return await m.reply("I can't guess the device!! woobs!!")
    
@WhiterX.on_callback_query(filters.regex(r"^d\.(.*?)\|(.*?)$"))
async def deviceinfo_callback(c: WhiterX, cb: CallbackQuery):
    try:
        device_id, user_id = cb.data.split('|')
    except ValueError:
        return print(cb.data)
    
    if cb.from_user.id != int(user_id):
        return await cb.answer(await tld(cb.message.chat.id, "NO_FOR_YOU"), show_alert=True)
    
    await cb.edit_message_text("[.!....]")

    device_id = re.sub(r"^d\.")

    link, img, description = await find_device(user_id, device_id)

    try:
        get_device_api = await get_device(device_id)
        name_cll = get_device_api.get("name", "N/A")
        base_device = f"<b>Photo Device:</b> <i>{img}</i>\n<b>Source URL:</b> <i>{link}</i>"
        DEVICE_TEXT = f"{base_device}\n\n📌 <b><u>{name_cll}</b></u>\n📅 <b>Announced:</b> <i>{get_device_api['detailSpec'][1]['specifications'][0]['value']}</i>"
        
        await cb.edit_message_text("[...!..]")

        for spec_index in range(14):
            try:
                base_category = get_device_api['detailSpec'][spec_index]['category']
                translated_category = CATEGORY_EMOJIS.get(base_category, '')
                category = gsmarena_tr_category(base_category, await tld(cb.message.chat.id, "language"))
                specs = get_device_api['detailSpec'][spec_index]['specifications']
                section_text = f"\n\n<b>{translated_category} <u>{category}</b></u>:\n"
                
                for spec in specs:
                    base_name = spec['name']
                    name = gsmarena_tr_info(base_name, await tld(cb.message.chat.id, "language"))
                    value = spec['value']
                    section_text += f"- <b>{name}:</b> <i>{value}</i>\n\n"
                        
                DEVICE_TEXT += section_text
            except (IndexError, KeyError):
                pass

        #Create Description
        DEVICE_TEXT += f"\n\n<b>Description</b>: <i>{description}</i>"

        await cb.edit_message_text("[.....!]")

        await del_device(user_id)
                
        try:
            await cb.edit_message_text(DEVICE_TEXT, disable_web_page_preview=False)
        except Exception as err:
            await c.delete_messages(cb.message.chat.id, cb.message.id)
            # Send the image with the first part of the caption
            caption_part = DEVICE_TEXT[:1024]
            caption_rest = DEVICE_TEXT[1024:]

            await c.send_photo(chat_id=cb.message.chat.id, photo=img, caption=caption_part)

            # Split the remaining caption and send as regular text messages
            message_chunks = [caption_rest[i:i + 4096] for i in range(0, len(caption_rest), 4096)]
            for chunk in message_chunks:
                await c.send_message(chat_id=cb.message.chat.id, text=chunk)
             
    except Exception as err:
        return await cb.edit_message_text(f"Couldn't retrieve device details. The GSM Arena website might be offline. <i>Error</i>: <b>{err}</b>\n<b>Line</b>: {err.__traceback__.tb_lineno}")
            

@WhiterX.on_message(filters.command(["twrp"], Config.TRIGGER))
async def twrp(c: WhiterX, m: Message):
    if not len(m.command) == 2:
        message = "Por favor, escreva seu codinome nele, ou seja, <code>/twrp herolte</code>"
        await m.reply_text(message)
        return
    device = m.command[1]
    url = await http.get(f"https://eu.dl.twrp.me/{device}/")
    if url.status_code == 404:
        await m.reply_text("TWRP atualmente não está disponível para <code>{}</code>".format(device))
    else:
        message = "<b>Último recovery TWRP para {}</b>\n".format(device)
        page = BeautifulSoup(url.content, "lxml")
        date = page.find("em").text.strip()
        message += "<b>Atualizado em:</b> <code>{}</code>\n".format(date)
        trs = page.find("table").find_all("tr")
        row = 2 if trs[0].find("a").text.endswith("tar") else 1
        for i in range(row):
            download = trs[i].find("a")
            dl_link = f"https://eu.dl.twrp.me{download['href']}"
            dl_file = download.text
            size = trs[i].find("span", {"class": "filesize"}).text
        message += "<b>Tamanho:</b> <code>{}</code>\n".format(size)
        message += "<b>Arquivo:</b> <code>{}</code>".format(dl_file.upper())
        keyboard = [[InlineKeyboardButton(text="Download", url=dl_link)]]
        await m.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

@WhiterX.on_message(filters.command(["magisk"], Config.TRIGGER))
async def magisk(c: WhiterX, m: Message):
    repo_url = "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/"
    text = await tld(m.chat.id, "MAGISK_STRING")
    for magisk_type in ["stable", "beta", "canary"]:
        fetch = await http.get(repo_url + magisk_type + ".json")
        data = rapidjson.loads(fetch.content)
        text += (
            f"<b>{magisk_type.capitalize()}</b>:\n"
            f'<a href="{data["magisk"]["link"]}" >Magisk - V{data["magisk"]["version"]}</a>'
            f' | <a href="{data["magisk"]["note"]}" >Changelog</a> \n'
        )
    await m.reply_text(text, disable_web_page_preview=True)

@WhiterX.on_message(filters.command(["app"], Config.TRIGGER))
async def app(c: WhiterX, message: Message):
    try:
        i = await message.reply(await tld(message.chat.id, "COM_2"))
        app_name = "+".join(message.text.split(" "))
        if not input_str(message):
            return await i.edit("<i>Eu preciso que você digite algo.</i>")
            
        res = requests.get(f"https://play.google.com/store/search?q={app_name}&c=apps")
        result = bs4.BeautifulSoup(res.text, "lxml")

        found = result.find("div", class_="vWM94c")
        if found:
            app_name = found.text
            app_dev = result.find("div", class_="LbQbAe").text
            app_rating = result.find(
                "div", class_="TT9eCd").text.replace("star", "")
            _app_link = result.find("a", class_="Qfxief")['href']
            app_icon = result.find("img", class_="T75of bzqKMd")['src']
        else:
            app_name = result.find("span", class_="DdYX5").text
            app_dev = result.find("span", class_="wMUdtb").text
            app_rating = result.find("span", class_="w2kbF").text
            _app_link = result.find("a", class_="Si6A0c Gy4nib")['href']
            app_icon = result.find("img", class_="T75of stzEZd")['src']

        app_dev_link = (
            "https://play.google.com/store/apps/developer?id="
            + app_dev.replace(" ", "+")
        )
        app_link = "https://play.google.com" + _app_link

        app_details = f"📲<b>{app_name}</b>\n\n"
        app_details += (await tld(message.chat.id, "APP_DEVELOPER")).format(app_dev, app_dev_link)
        app_details += (await tld(message.chat.id, "APP_RATING")).format(app_rating)
        keyboard = [[InlineKeyboardButton(await tld(message.chat.id, "VIEW_IN_PLAYSTORE_BNT"), url=app_link)]]
        await message.reply_photo(app_icon, caption=app_details, reply_markup=InlineKeyboardMarkup(keyboard))
        await i.delete()
    except IndexError:
        await i.edit("<i>No result found in search. Please enter</i> <b>Valid app name</b>")
    except Exception as err:
        await i.edit(err)

@WhiterX.on_message(filters.command(["device", "whatis"], Config.TRIGGER))
async def device_(_, message: Message):
    if not len(message.command) == 2:
        await message.reply(await tld(message.chat.id, "DEVICE_NO_CODENAME"))
        return
    msg = await message.reply(await tld(message.chat.id, "COM_2"))
    getlist = requests.get(DEVICE_LIST).json()
    target_device = message.text.split()[1].lower()
    if target_device in list(getlist):
        device = getlist.get(target_device)
        text = ""
        for x in device:
            brand = x['brand']
            name = x['name']
            model = x['model']
            text += (await tld(message.chat.id, "DEVICE_SUCCESS")).format(brand, name, model, target_device)
            text += "\n\n"
        await msg.edit(text)
    else:
        await msg.edit((await tld(message.chat.id, "DEVICE_NOT_FOUND")).format(target_device))
        await asyncio.sleep(5)
        await msg.delete()


__help__ = True
