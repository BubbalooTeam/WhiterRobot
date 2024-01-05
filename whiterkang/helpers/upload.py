import datetime
import asyncio
import os

from . import get_progress, tld, humanbytes
from .. import WhiterX, Config

from hydrogram.types import Message
from pyrogram.errors import FloodWait, MessageNotModified
from hydrogram.enums import ChatAction, ParseMode

from typing import Union, Tuple
from urllib.parse import unquote_plus
from pySmartDL import SmartDL
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pathlib import Path

class Uploader:
    async def doc_upload(self, m: Message, path, del_path: bool = False, extra: str = '', with_thumb: bool = True):
        str_path = str(path)
        sent: Message = await WhiterX.send_message(
            m.chat.id, f"<code>Uploading {str_path} as a doc ... {extra}</code>")
        start_t = datetime.datetime.now()
        await WhiterX.send_chat_action(m.chat.id, ChatAction.UPLOAD_DOCUMENT)
        try:
            msg = await WhiterX.send_document(
                chat_id=m.chat.id,
                document=str_path,
                caption=path.name,
                parse_mode=ParseMode.HTML,
                force_document=True,
                disable_notification=True,
            )
        except ValueError as e_e:
            await sent.edit(f"Skipping <code>{str_path}</code> due to {e_e}")
        except Exception as u_e:
            await sent.edit(str(u_e))
            raise u_e
        else:
            await sent.delete()
            await self.finalize(msg, start_t)
            if os.path.exists(str_path) and del_path:
                os.remove(str_path)


    async def vid_upload(self, m: Message, path, del_path: bool = False, extra: str = '', with_thumb: bool = True):
        str_path = str(path)
        duration = 0
        metadata = extractMetadata(createParser(str_path))
        if metadata and metadata.has("duration"):
            duration = metadata.get("duration").seconds
        sent: Message = await WhiterX.send_message(
            m.chat.id, f"<code>Uploading {str_path} as a video ... {extra}</code>")
        start_t = datetime.datetime.now()
        await WhiterX.send_chat_action(m.chat.id, ChatAction.UPLOAD_VIDEO)
        width = 0
        height = 0
        try:
            msg = await WhiterX.send_video(
                chat_id=m.chat.id,
                video=str_path,
                duration=duration,
                width=width,
                height=height,
                caption=path.name,
                parse_mode=ParseMode.HTML,
                disable_notification=True,
            )
        except ValueError as e_e:
            await sent.edit(f"Skipping <code>{str_path}</code> due to {e_e}")
        except Exception as u_e:
            await sent.edit(str(u_e))
            raise u_e
        else:
            await sent.delete()
            await self.finalize(msg, start_t)
            if os.path.exists(str_path) and del_path:
                os.remove(str_path)


    async def audio_upload(self, m: Message, path, del_path: bool = False, extra: str = '', with_thumb: bool = True):
        title = None
        artist = None
        thumb = None
        duration = 0
        str_path = str(path)
        file_size = humanbytes(os.stat(str_path).st_size)
        metadata = extractMetadata(createParser(str_path))
        if metadata and metadata.has("title"):
            title = metadata.get("title")
        if metadata and metadata.has("artist"):
            artist = metadata.get("artist")
        if metadata and metadata.has("duration"):
            duration = metadata.get("duration").seconds
        sent: Message = await WhiterX.send_message(
            m.chat.id, f"<code>Uploading {str_path} as audio ... {extra}</code>")
        start_t = datetime.datetime.now()
        await WhiterX.send_chat_action(m.chat.id, ChatAction.UPLOAD_AUDIO)
        try:
            msg = await WhiterX.send_audio(
                chat_id=m.chat.id,
                audio=str_path,
                caption=f"{path.name}\n[ {file_size} ]",
                title=title,
                performer=artist,
                duration=duration,
                parse_mode=ParseMode.HTML,
                disable_notification=True,
            )
        except ValueError as e_e:
            await sent.edit(f"Skipping <code>{str_path}</code> due to {e_e}")
        except Exception as u_e:
            await sent.edit(str(u_e))
            raise u_e
        else:
            await sent.delete()
            await self.finalize(msg, start_t)
            if os.path.exists(str_path) and del_path:
                os.remove(str_path)

    async def photo_upload(self, m: Message, path, del_path: bool = False, extra: str = ''):
        str_path = str(path)
        sent: Message = await WhiterX.send_message(
            m.chat.id, f"<code>Uploading {path.name} as photo ... {extra}</code>")
        start_t = datetime.datetime.now()
        await WhiterX.send_chat_action(m.chat.id, ChatAction.UPLOAD_PHOTO)
        try:
            msg = await WhiterX.send_photo(
                chat_id=m.chat.id,
                photo=str_path,
                caption=path.name,
                parse_mode=ParseMode.HTML,
                disable_notification=True,
            )
        except ValueError as e_e:
            await sent.edit(f"Skipping <code>{str_path}</code> due to {e_e}")
        except Exception as u_e:
            await sent.edit(str(u_e))
            raise u_e
        else:
            await sent.delete()
            await self.finalize(msg, start_t)
            if os.path.exists(str_path) and del_path:
                os.remove(str_path)


    async def finalize(self, msg: Message, start_t):
        end_t = datetime.datetime.now()
        m_s = (end_t - start_t).seconds
        await msg.edit(f"<code>Uploaded in {m_s} seconds</code>")

    async def url_download(self, m: Message, url: str) -> Tuple[str, int]:
        """download from link"""
        msg = await m.reply(await tld(m.chat.id, "DOWNLOAD_YT"))
        start_t = datetime.datetime.now()
        custom_file_name = unquote_plus(os.path.basename(url))
        if "|" in url:
            url, c_file_name = url.split("|", maxsplit=1)
            url = url.strip()
            if c_file_name:
                custom_file_name = c_file_name.strip()
        dl_loc = os.path.join(Config.DOWN_PATH, custom_file_name)
        downloader = SmartDL(url, dl_loc, progress_bar=False)
        downloader.start(blocking=False)
        count = 0
        while not downloader.isFinished():
            total_length = downloader.filesize or 0
            downloaded = downloader.get_dl_size()
            percentage = downloader.get_progress() * 100
            speed = downloader.get_speed(human=True)
            estimated_total_time = downloader.get_eta(human=True)
            count += 1
            if count >= 10:
                count = 0
            await asyncio.sleep(2)
            try:
                await msg.edit((await tld(m.chat.id, "DOWNLOAD_UPLOAD")).format(get_progress(percentage), int(round(percentage)), estimated_total_time))
            except MessageNotModified:
                continue
            except FloodWait as tm:
                await asyncio.sleep(tm.value)
                continue
        await msg.edit(await tld(m.chat.id, "UPLOAD_DOWNLOAD_FINISHED"))
        await asyncio.sleep(5)
        await msg.delete()
        return dl_loc, (datetime.datetime.now() - start_t).seconds

    async def upload_path(self, m: Message, path: Path, del_path: bool):
        file_paths = []
        if path.exists():
            async def explorer(_path: Path) -> None:
                if _path.is_file() and _path.stat().st_size:
                    file_paths.append(_path)
                elif _path.is_dir():
                    for i in sorted(_path.iterdir(), key=lambda a: (a.name)):
                        await explorer(i)
            await explorer(path)
        else:
            path = path.expanduser()
            str_path = os.path.join(*(path.parts[1:] if path.is_absolute() else path.parts))
            for p in Path(path.root).glob(str_path):
                file_paths.append(p)
        current = 0
        for p_t in file_paths:
            current += 1
            try:
                await self.upload(m, p_t, del_path, f"{current}/{len(file_paths)}")
            except FloodWait as f_e:
                await asyncio.sleep(f_e.value)  

    async def upload(self, m: Message, path: Path, del_path: bool = False, extra: str = '', with_thumb: bool = True):
        if path.name.lower().endswith(
            (".mkv", ".mp4", ".webm", ".m4v")):
            await self.vid_upload(m, path, del_path, extra, with_thumb)
        elif path.name.lower().endswith(
            (".mp3", ".flac", ".wav", ".m4a")):
            await self.audio_upload(m, path, del_path, extra, with_thumb)
        elif path.name.lower().endswith(
            (".jpg", ".jpeg", ".png", ".bmp", ".webp")):
            await self.photo_upload(m, path, del_path, extra)
        else:
            await self.doc_upload(m, path, del_path, extra, with_thumb)


upclient = Uploader()