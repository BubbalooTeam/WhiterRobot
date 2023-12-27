import random
import re
from zalgo_text import zalgo

from hydrogram import filters
from hydrogram.types import Message
from hydrogram.enums import ChatType

from whiterkang import WhiterX, Config
from whiterkang.helpers import input_str, tld, disableable_dec, find_gp, add_gp

WIDE_MAP = {i: i + 0xFEE0 for i in range(0x21, 0x7F)}
WIDE_MAP[0x20] = 0x3000

@WhiterX.on_message(filters.command("owo", Config.TRIGGER))
async def owo(c: WhiterX, m: Message):
    if m.chat.type != ChatType.PRIVATE:
        if not await find_gp(m.chat.id):
            await add_gp(m)
    noreply = False
    if m.reply_to_message and m.reply_to_message.text:
        data = m.reply_to_message.text
    elif input_str(m):
        noreply = True
        data = input_str(m)
    else:
        noreply = True
        data = await tld(m.chat.id, "MEMES_NO_MESSAGE")

    faces = [
        '(・`ω´・)', ';;w;;', 'owo', 'UwU', '>w<', '^w^', '\(^o\) (/o^)/',
        '( ^ _ ^)∠☆', '(ô_ô)', '~:o', ';____;', '(*^*)', '(>_', '(♥_♥)',
        '*(^O^)*', '((+_+))'
    ]
    reply_text = re.sub(r'[rl]', "w", data)
    reply_text = re.sub(r'[ｒｌ]', "ｗ", data)
    reply_text = re.sub(r'[RL]', 'W', reply_text)
    reply_text = re.sub(r'[ＲＬ]', 'Ｗ', reply_text)
    reply_text = re.sub(r'n([aeiouａｅｉｏｕ])', r'ny\1', reply_text)
    reply_text = re.sub(r'ｎ([ａｅｉｏｕ])', r'ｎｙ\1', reply_text)
    reply_text = re.sub(r'N([aeiouAEIOU])', r'Ny\1', reply_text)
    reply_text = re.sub(r'Ｎ([ａｅｉｏｕＡＥＩＯＵ])', r'Ｎｙ\1', reply_text)
    reply_text = re.sub(r'\!+', ' ' + random.choice(faces), reply_text)
    reply_text = re.sub(r'！+', ' ' + random.choice(faces), reply_text)
    reply_text = reply_text.replace("ove", "uv")
    reply_text = reply_text.replace("ｏｖｅ", "ｕｖ")
    reply_text += ' ' + random.choice(faces)

    if noreply:
        await m.reply(reply_text)
    else:
        m.reply_to_message.reply(reply_text)

@WhiterX.on_message(filters.command("stretch", Config.TRIGGER))
async def stretch(c: WhiterX, m: Message):
    if m.chat.type != ChatType.PRIVATE:
        if not await find_gp(m.chat.id):
            await add_gp(m)
    noreply = False
    if m.reply_to_message and m.reply_to_message.text:
        data = m.reply_to_message.text
    elif input_str(m):
        noreply = True
        data = input_str(m)
    else:
        noreply = True
        data = await tld(m.chat.id, "MEMES_NO_MESSAGE")

    count = random.randint(3, 10)
    reply_text = re.sub(r'([aeiouAEIOUａｅｉｏｕＡＥＩＯＵ])', (r'\1' * count), data)

    if noreply:
        await m.reply(reply_text)
    else:
        await m.reply_to_message.reply(reply_text)

@WhiterX.on_message(filters.command("vapor", Config.TRIGGER))
async def vapor(c: WhiterX, m: Message):
    if m.chat.type != ChatType.PRIVATE:
        if not await find_gp(m.chat.id):
            await add_gp(m)
    noreply = False
    if m.reply_to_message and m.reply_to_message.text:
        data = m.reply_to_message.text
    elif input_str(m):
        noreply = True
        data = input_str(m)
    else:
        noreply = True
        data = await tld(m.chat.id, "MEMES_NO_MESSAGE")

    reply_text = str(data).translate(WIDE_MAP)

    if noreply:
        await m.reply(reply_text)
    else:
        await m.reply_to_message.reply(reply_text)

@WhiterX.on_message(filters.command("zalgo", Config.TRIGGER))
async def zalgo_text(c: WhiterX, m: Message):
    if m.chat.type != ChatType.PRIVATE:
        if not await find_gp(m.chat.id):
            await add_gp(m)
    noreply = False
    if m.reply_to_message and m.reply_to_message.text:
        data = m.reply_to_message.text
    elif input_str(m):
        noreply = True
        data = input_str(m)
    else:
        noreply = True
        data = await tld(m.chat.id, "MEMES_NO_MESSAGE")

    reply_text = zalgo.zalgo().zalgofy(data)

    if noreply:
        await m.reply(reply_text)
    else:
        await m.reply_to_message.reply(reply_text)

@WhiterX.on_message(filters.command("insults", Config.TRIGGER))
async def insults(c: WhiterX, m: Message):
    if m.chat.type != ChatType.PRIVATE:
        if not await find_gp(m.chat.id):
            await add_gp(m)
    text = random.choice(await tld(m.chat.id, "MEMES_INSULTS_LIST"))

    if m.reply_to_message:
        await m.reply_to_message.reply(text)
    else:
        await m.reply(text)

@WhiterX.on_message(filters.command("runs", Config.TRIGGER))
async def runs(c: WhiterX, m: Message):
    if m.chat.type != ChatType.PRIVATE:
        if not await find_gp(m.chat.id):
            await add_gp(m)
    text = random.choice(await tld(m.chat.id, "MEMES_RUNS_LIST"))

    await m.reply(text)

@WhiterX.on_message(filters.command("slap", Config.TRIGGER))
async def slap(c: WhiterX, m: Message):
    if m.chat.type != ChatType.PRIVATE:
        if not await find_gp(m.chat.id):
            await add_gp(m)
    # reply to correct message
    reply_text = m.reply_to_message.reply if m.reply_to_message else m.reply

    # get user who sent message
    if m.from_user.username:
        curr_user = "@" + m.from_user.username
    else:
        curr_user = m.from_user.mention

    if input_str(m):
        user = await c.get_users(input_str(m))
        user_id = user.id
    elif m.reply_to_message and m.reply_to_message.from_user:
        user = await c.get_users(m.reply_to_message.from_user.id)
        user_id = user.id
    else:
        user = None
        user_id = None
    if user_id != None:
        slapped_user = await c.get_users(user_id)
        user1 = curr_user

        if slapped_user.username == "DaviTudo":
            await reply_text(await tld(m.chat.id, "MEMES_NOT_DOING_THAT"))
            return
        
        if slapped_user.username:
            user2 = "@" + slapped_user.username
        else:
            user2 = slapped_user.mention

    # if no target found, bot targets the sender
    else:
        user1 = (await WhiterX.get_me()).mention
        user2 = curr_user

    temp = random.choice(await tld(m.chat.id, "MEMES_SLAPS_TEMPLATES_LIST"))
    item = random.choice(await tld(m.chat.id, "MEMES_ITEMS_LIST"))
    hit = random.choice(await tld(m.chat.id, "MEMES_HIT_LIST"))
    throw = random.choice(await tld(m.chat.id, "MEMES_THROW_LIST"))
    itemp = random.choice(await tld(m.chat.id, "MEMES_ITEMS_LIST"))
    itemr = random.choice(await tld(m.chat.id, "MEMES_ITEMS_LIST"))

    repl = temp.format(user1=user1,
                       user2=user2,
                       item=item,
                       hits=hit,
                       throws=throw,
                       itemp=itemp,
                       itemr=itemr)

    await reply_text(repl)    
