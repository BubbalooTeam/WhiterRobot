import os
import shutil
import tempfile
import math
import filetype

from whiterkang import WhiterX, Config
from whiterkang.helpers import tld, disableable_dec, EMOJI_PATTERN, convert_video, resize_image, http

from hydrogram import filters
from hydrogram.errors import PeerIdInvalid, StickersetInvalid
from hydrogram.raw.functions.messages import GetStickerSet, SendMedia
from hydrogram.raw.functions.stickers import AddStickerToSet, CreateStickerSet
from hydrogram.raw.types import (
    DocumentAttributeFilename,
    InputDocument,
    InputMediaUploadedDocument,
    InputStickerSetItem,
    InputStickerSetShortName,
)
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton


SUPPORTED_TYPES = ["jpeg", "png", "webp"]

@WhiterX.on_message(filters.command(["getsticker"], Config.TRIGGER))
@disableable_dec("getsticker")
async def getsticker_(c: WhiterX, m: Message):
    sticker = m.reply_to_message.sticker
    if sticker:
        if sticker.is_animated:
            await m.reply_text(("Stickers Animados, Não são suportados!"))
        else:
            extension = ".png" if not sticker.is_video else ".webm"
            file = await m.reply_to_message.download(
                in_memory=True, file_name=f"{sticker.file_unique_id}.{extension}"
            )

        await m.reply_to_message.reply_document(
            document=file,
            caption=("<b>Emoji:</b> {}\n<b>Sticker ID:</b> <code>{}</code>\n\n<b>Send By: @WhiterKangBOT</b>").format(
                sticker.emoji, sticker.file_id
            ),
        )
    else:
        await m.reply_text(
            (
                "Responda a um adesivo com esse comando para que eu possa enviá-lo para você como \
<b>Arquivo .png ou .gif</b>.\n<i>Só funcionara com vídeos e adesivos estáticos</i>"
            )
        )


@WhiterX.on_message(filters.command("stickerid", Config.TRIGGER) & filters.reply)
@disableable_dec("stickerid")
async def getstickerid(c: WhiterX, m: Message):
    if m.reply_to_message.sticker:
        await m.reply_text(
            "O id deste sticker é: <code>{stickerid}</code>".format(
                stickerid=m.reply_to_message.sticker.file_id
            )
        )


@WhiterX.on_message(filters.command(["kibe", "kang"], Config.TRIGGER))
@disableable_dec("kang")
async def kang(c: WhiterX, m: Message):
    progress_mesage = await m.reply_text(await tld(m.chat.id, "KANGING"))
    emoji = "🤔"
    packnum = 0
    packname_found = False
    resize = False
    animated = False
    videos = False
    convert = False
    if m.reply_to_message and m.reply_to_message.media:
        if (
            not m.reply_to_message.photo
            and m.reply_to_message.document
            and "image" in m.reply_to_message.document.mime_type
            or m.reply_to_message.photo
        ):
            resize = True
        elif (
            m.reply_to_message.document
            and "tgsticker" in m.reply_to_message.document.mime_type
        ):
            animated = True
        elif (
            m.reply_to_message.document
            and "video" in m.reply_to_message.document.mime_type
            or m.reply_to_message.video
            or m.reply_to_message.animation
        ):
            convert = True
            videos = True
        elif m.reply_to_message.sticker:
            if not m.reply_to_message.sticker.file_name:
                return await progress_mesage.edit_text(await tld(m.chat.id, "STICKER_NOT_NAME"))
            if m.reply_to_message.sticker.emoji:
                emoji = m.reply_to_message.sticker.emoji
            animated = m.reply_to_message.sticker.is_animated
            videos = m.reply_to_message.sticker.is_video
            if not m.reply_to_message.sticker.file_name.endswith(".tgs") and not videos:
                resize = True
        else:
            return await progress_mesage.edit_text(await tld(m.chat.id, "NO_STICKER_SUPORTED"))

        pack_prefix = "anim" if animated else "vid" if videos else "a"
        packname = f"{pack_prefix}_{m.from_user.id}_by_{c.me.username}"

        if (
            len(m.command) > 1
            and m.command[1].isdigit()
            and int(m.command[1]) > 0
        ):
            # provide pack number to kang in desired pack
            packnum = m.command.pop(1)
            packname = f"{pack_prefix}{packnum}_{m.from_user.id}_by_{c.me.username}"
        if len(m.command) > 1:
            # matches all valid emojis in input
            emoji = "".join(set(EMOJI_PATTERN.findall("".join(m.command[1:])))) or emoji

        if convert:
            file = await c.download_media(m.reply_to_message)
        else:
            file = await c.download_media(m.reply_to_message, in_memory=True)
        if not file:
            await progress_mesage.delete()  # Failed to download
            return None
    else:
        return await progress_mesage.edit_text(await tld(m.chat.id, "STICKER_NO_REPLY"))

    try:
        if resize:
            file = resize_image(file)
        elif convert:
            file = await convert_video(file)
            file.name = f"sticker.{filetype.guess_extension(file)}"
            await progress_mesage.edit_text(await tld(m.chat.id, "CONVERTING_VIDEO"))
            if file is False:
                return await progress_mesage.edit_text("<b>Error</b>")
        max_stickers = 50 if animated else 120
        while not packname_found:
            try:
                stickerset = await c.invoke(
                    GetStickerSet(
                        stickerset=InputStickerSetShortName(short_name=packname),
                        hash=0,
                    )
                )
                if stickerset.set.count >= max_stickers:
                    packnum += 1
                    packname = (
                        f"{pack_prefix}_{packnum}_{m.from_user.id}_by_{c.me.username}"
                    )
                else:
                    packname_found = True
            except StickersetInvalid:
                break
        ufile = await c.save_file(file)
        media = await c.invoke(
            SendMedia(
                peer=(await c.resolve_peer(int(Config.GP_LOGS))),
                media=InputMediaUploadedDocument(
                    file=ufile,
                    mime_type=filetype.guess_mime(file),
                    attributes=[DocumentAttributeFilename(file_name=file.name)],
                ),
                message=f"#Sticker kang by UserID -> {m.from_user.id}",
                random_id=c.rnd_id(),
            ),
        )
        msg_ = media.updates[-1].message
        stkr_file = msg_.media.document
        if packname_found:
            await progress_mesage.edit_text(await tld(m.chat.id, "USE_EXISTING_PACK"))
            await c.invoke(
                AddStickerToSet(
                    stickerset=InputStickerSetShortName(short_name=packname),
                    sticker=InputStickerSetItem(
                        document=InputDocument(
                            id=stkr_file.id,
                            access_hash=stkr_file.access_hash,
                            file_reference=stkr_file.file_reference,
                        ),
                        emoji=emoji,
                    ),
                )
            )
        else:
            await progress_mesage.edit_text(await tld(m.chat.id, "CREATE_STICKER_PACK"))
            try:
                stkr_title = f"@{m.from_user.username[:32]}'s WhiterRobot"
            except TypeError:
                stkr_title = f"@{m.from_user.username[:32]}'s WhiterRobot"
            if animated:
                stkr_title += " AnimPack"
            elif videos:
                stkr_title += " VidPack"
            if packnum != 0:
                stkr_title += f" v{packnum}"
            try:
                await c.invoke(
                    CreateStickerSet(
                        user_id=await c.resolve_peer(
                            m.from_user.username or m.from_user.id
                        ),
                        title=stkr_title,
                        short_name=packname,
                        stickers=[
                            InputStickerSetItem(
                                document=InputDocument(
                                    id=stkr_file.id,
                                    access_hash=stkr_file.access_hash,
                                    file_reference=stkr_file.file_reference,
                                ),
                                emoji=emoji,
                            )
                        ],
                        animated=animated,
                        videos=videos,
                    )
                )
            except PeerIdInvalid:
                return await progress_mesage.edit_text(
                    await tld(m.chat.id, "STICKERS_NOT_FOUND_USER"),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "/start", url=f"https://t.me/{c.me.username}?start"
                                )
                            ]
                        ]
                    ),
                )
    except Exception as all_e:
        await progress_mesage.edit_text(f"{all_e.__class__.__name__} : {all_e}")
    else:
        await progress_mesage.edit_text((await tld(m.chat.id, "STICKERS_KANGED")).format(packname, emoji))
        await c.delete_messages(chat_id=Config.GP_LOGS, message_ids=msg_.id, revoke=True)

__help__ = True
