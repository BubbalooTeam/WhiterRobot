import contextlib
import io
import re
import json
import uuid
import esprima
import filetype


from bs4 import BeautifulSoup as bs
from httpx import AsyncClient
from yt_dlp import YoutubeDL
from yt_dlp.utils import ExtractorError
from typing import List, Dict, Union, Any

from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict

from whiterkang import Config
from .tools import http, aiowrap, humanbytes         

proxys = {
    "PROXIES":
    [
        "https://47.252.20.42:8058",
        "https://47.88.11.3:3128",
        "https://8.213.128.90:808",
        "http://localhost:4030",
        "http://localhost:8000"
    ]
    
}

YT = "https://www.youtube.com/"
YT_VID_URL = YT + "watch?v="

def sublists(input_list: List[Any], width: int = 3) -> List[List[Any]]:
    """retuns a single list of multiple sublist of fixed width"""
    return [input_list[x : x + width] for x in range(0, len(input_list), width)]
          

@aiowrap
def extract_info(instance: YoutubeDL, url: str, download=True):
    return instance.extract_info(url, download)

class DownloadMedia:
    def __init__(self):
        self.TwitterAPI: str = "https://api.twitter.com/2/"
        self.ThreadsAPI: str = "https://www.threads.net/api/graphql"

    async def download(self, url: str, captions: bool):
        self.files: list = []
        self.caption = f"<a href='{url}'>🔗 Link</a>"
        if re.search(r"instagram.com/", url):
            await self.Instagram(url, captions)
        elif re.search(r"tiktok.com/", url):
            await self.TikTok(url, captions)
        elif re.search(r"(twitter|x).com/", url):
            await self.Twitter(url, captions)
        elif re.search(r"threads.net/", url):
            await self.Threads(url, captions)

        if not captions:
            self.caption = f"<a href='{url}'>🔗 Link</a>"
        return self.files, self.caption

    async def httpx(self, url: str):
        if (await http.get(url)).status_code != 200:
            for proxy in proxys["PROXIES"]:
                http_client = AsyncClient(proxies=proxy)
                response = await http_client.get(url)
                if response.status_code == 200:
                    break
            return http_client
        else:  # noqa: RET505
            return http

    async def downloader(self, url: str, width: int, height: int):
        """
        Get the media from URL.

        Arguments:
            url (str): The URL of the post and res info.

        Returns:
            Dict: Media url and res info.
        """
        file = io.BytesIO((await http.get(url)).content)
        file.name = f"{url[60:80]}.{filetype.guess_extension(file)}"
        self.files.append({"p": file, "w": width, "h": height})

    async def Instagram(self, url: str, captions: str):
        headers = {
            "authority": "www.instagram.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp\
,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "max-age=0",
            "sec-fetch-mode": "navigate",
            "upgrade-insecure-requests": "1",
            "referer": "https://www.instagram.com/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 \
(KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36",
            "viewport-width": "1280",
        }

        if regex := re.search(r"(?:reel|p)/([A-Za-z0-9_-]+)", url):
            post_id = regex.group(1)
        else:
            return

        httpx = await self.httpx("https://www.instagram.com/")

        r = await httpx.get(
            f"https://www.instagram.com/p/{post_id}/embed/captioned",
            headers=headers,
            follow_redirects=True,
        )
        soup = bs(r.text, "html.parser")

        if soup.find("div", {"data-media-type": "GraphImage"}):
            caption = re.sub(
                r'.*</a><br/><br/>(.*)(<div class="CaptionComments">.*)',
                r"\1",
                str(soup.find("div", {"class": "Caption"})),
            ).replace("<br/>", "\n")
            self.caption = f"{caption}\n<a href='{url}'>🔗 Link</a>"
            file = soup.find("img", {"class": "EmbeddedMediaImage"}).get("src")
            await self.downloader(file, 0, 0)

        data = re.findall(r'<script>(requireLazy\(\["TimeSliceImpl".*)<\/script>', r.text)
        if data and "shortcode_media" in data[0]:
            tokenized = esprima.tokenize(data[0])
            for token in tokenized:
                if "shortcode_media" in token.value:
                    jsoninsta = json.loads(json.loads(token.value))["gql_data"]["shortcode_media"]

                    if caption := jsoninsta["edge_media_to_caption"]["edges"]:
                        self.caption = f"{caption[0]['node']['text']}\n<a href='{url}'>🔗 Link</a>"
                    else:
                        self.caption = f"\n<a href='{url}'>🔗 Link</a>"

                    if jsoninsta["__typename"] == "GraphVideo":
                        await self.downloader(
                            jsoninsta["video_url"],
                            jsoninsta["dimensions"]["width"],
                            jsoninsta["dimensions"]["height"],
                        )
                    else:
                        for post in jsoninsta["edge_sidecar_to_children"]["edges"]:
                            url = post["node"]["display_url"]
                            if post["node"]["is_video"] is True:
                                with contextlib.suppress(KeyError):
                                    url = post["node"]["video_url"]
                            dimensions = post["node"]["dimensions"]
                            await self.downloader(
                                url,
                                dimensions["width"],
                                dimensions["height"],
                            )
        else:
            r = await httpx.get(
                f"https://www.instagram.com/p/{post_id}/",
                headers=headers,
            )
            soup = bs(r.text, "html.parser")
            if content := soup.find("script", type="application/ld+json"):
                data = json.loads(content.contents[0])
            else:
                return

            if "video" in data[0]:
                video = data[0]["video"]
                if len(video) == 1:
                    await self.downloader(
                        video[0]["contentUrl"], int(video[0]["width"]), int(video[0]["height"])
                    )
                else:
                    for v in video:
                        await self.downloader(v["contentUrl"], v["width"], v["height"])

    async def Twitter(self, url: str, captions: str):
        bearer: str = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7tt\
fk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"  # Twitter Bearer Token
        # Extract the tweet ID from the URL
        tweet_id = re.match(".*(twitter|x).com/.+status/([A-Za-z0-9]+)", url)[2]
        csrfToken = str(uuid.uuid4()).replace("-", "")
        headers = {
            "Authorization": bearer,
            "Cookie": f"auth_token=ee4ebd1070835b90a9b8016d1e6c6130ccc89637; ct0={csrfToken}; ",
            "x-twitter-active-user": "yes",
            "x-twitter-auth-type": "OAuth2Session",
            "x-twitter-client-language": "en",
            "x-csrf-token": csrfToken,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 \
Firefox/116.0",
        }

        params = {
            "variables": json.dumps(
                {
                    "focalTweetId": tweet_id,
                    "referrer": "messages",
                    "includePromotedContent": True,
                    "withCommunity": True,
                    "withQuickPromoteEligibilityTweetFields": True,
                    "withBirdwatchNotes": True,
                    "withVoice": True,
                    "withV2Timeline": True,
                }
            ),
            "features": json.dumps(
                {
                    "rweb_lists_timeline_redesign_enabled": True,
                    "responsive_web_graphql_exclude_directive_enabled": True,
                    "verified_phone_label_enabled": False,
                    "creator_subscriptions_tweet_preview_api_enabled": True,
                    "responsive_web_graphql_timeline_navigation_enabled": True,
                    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                    "tweetypie_unmention_optimization_enabled": True,
                    "responsive_web_edit_tweet_api_enabled": True,
                    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": False,
                    "view_counts_everywhere_api_enabled": True,
                    "longform_notetweets_consumption_enabled": True,
                    "responsive_web_twitter_article_tweet_consumption_enabled": False,
                    "tweet_awards_web_tipping_enabled": False,
                    "freedom_of_speech_not_reach_fetch_enabled": True,
                    "standardized_nudges_misinfo": True,
                    "tweet_with_visibility_results_prefer_gql\
_limited_actions_policy_enabled": True,
                    "longform_notetweets_rich_text_read_enabled": True,
                    "longform_notetweets_inline_media_enabled": True,
                    "responsive_web_media_download_video_enabled": False,
                    "responsive_web_enhance_cards_enabled": False,
                }
            ),
            "fieldToggles": json.dumps(
                {"withAuxiliaryUserLabels": False, "withArticleRichContentState": False}
            ),
        }

        r = (
            await http.get(
                "https://twitter.com/i/api/graphql/NmCeCgkVlsRGS1cAwqtgmw/TweetDetail",
                params=params,
                headers=headers,
            )
        ).json()

        try:
            res = r["data"]["threaded_conversation_with_injections_v2"]["instructions"][0][
                "entries"
            ]

            for entries in res:
                if tweet_id in entries["entryId"]:
                    tweet = entries["content"]["itemContent"]["tweet_results"]["result"]

            if tweet["__typename"] == "TweetWithVisibilityResults":
                tweet = tweet["tweet"]

            user_name = tweet["core"]["user_results"]["result"]["legacy"]["name"]
            self.caption = f"<b>{user_name}</b>\n{tweet['legacy']['full_text']}"

            for media in tweet["legacy"]["extended_entities"]["media"]:
                if media["type"] in ("animated_gif", "video"):
                    bitrate = [
                        a["bitrate"]
                        for a in media["video_info"]["variants"]
                        if a["content_type"] == "video/mp4"
                    ]
                    for a in media["video_info"]["variants"]:
                        if a["content_type"] == "video/mp4" and a["bitrate"] == max(bitrate):
                            url = a["url"]

                    await self.downloader(
                        url,
                        media["original_info"]["width"],
                        media["original_info"]["height"],
                    )
                else:
                    await self.downloader(
                        media["media_url_https"],
                        media["original_info"]["width"],
                        media["original_info"]["height"],
                    )
        except KeyError:
            return

    async def TikTok(self, url: str, captions: str):
        id = io.StringIO()
        x = re.match(r".*tiktok.com\/.*?(:?@[A-Za-z0-9]+\/video\/)?([A-Za-z0-9]+)", url)
        ydl = YoutubeDL({"outtmpl": f"{Config.DOWN_PATH}{id}/{x[2]}.%(ext)s"})
        yt = await extract_info(ydl, url, download=True)
        self.caption = f"{yt['title']}\n\n<a href='{url}'>🔗 Link</a>"
        self.files.append(
            {
                "p": f"{Config.DOWN_PATH}{id}/{x[2]}.mp4",
                "w": yt["formats"][0]["width"],
                "h": yt["formats"][0]["height"],
            }
        )

    async def Threads(self, url: str, captions: str):
        httpx = await self.httpx("https://www.threads.net/")
        post_id = re.findall(r'{"post_id":"(\d+)"}', (await httpx.get(url)).text)[0]

        response = await httpx.post(
            self.ThreadsAPI,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-IG-App-ID": "238260118697367",
                "X-FB-LSD": "LFEwwEJ6qDWEUM-79Hlmgq",
                "Sec-Fetch-Site": "same-origin",
            },
            data={
                "lsd": "LFEwwEJ6qDWEUM-79Hlmgq",
                "variables": json.dumps(
                    {
                        "postID": post_id,
                    }
                ),
                "doc_id": "5587632691339264",
            },
        )
        r = response.json()
        thread = r["data"]["data"]["containing_thread"]["thread_items"][0]["post"]

        if thread["caption"] is not None:
            self.caption = f"{thread['caption']['text']}\n<a href='{url}'>🔗 Link</a>"

        if len(thread["video_versions"]) == 0:
            if thread["carousel_media"] is not None:
                for media in thread["carousel_media"]:
                    if len(media["video_versions"]) == 0:
                        await self.downloader(
                            media["image_versions2"]["candidates"][0]["url"],
                            thread["original_width"],
                            thread["original_height"],
                        )
                    else:
                        await self.downloader(
                            media["video_versions"][0]["url"],
                            thread["original_width"],
                            thread["original_height"],
                        )
            else:
                info = thread["image_versions2"]["candidates"][0]
                await self.downloader(info["url"], info["width"], info["height"])
        else:
            url = thread["video_versions"][0]["url"]
            await self.downloader(url, thread["original_width"], thread["original_height"])


class Buttons(InlineKeyboardMarkup):
    def __init__(self, inline_keyboard: List[List["InlineKeyboardButton"]]):
        super().__init__(inline_keyboard)

    def __add__(self, extra: Union[str, int]) -> InlineKeyboardMarkup:
        """Add extra Data to callback_data of every button

        Parameters:
        ----------
            - extra (`Union[str, int]`): Extra data e.g A `key` or `user_id`.

        Raises:
        ------
            `TypeError`

        Returns:
        -------
            `InlineKeyboardMarkup`: Modified markup
        """
        if not isinstance(extra, (str, int)):
            raise TypeError(
                f"unsupported operand `extra` for + : '{type(extra)}' and '{type(self)}'"
            )
        ikb = self.inline_keyboard
        cb_extra = f"-{extra}"
        for row in ikb:
            for btn in row:
                if (
                    (cb_data := btn.callback_data)
                    and cb_data.startswith("yt_")
                    and not cb_data.endswith(cb_extra)
                ):
                    cb_data += cb_extra
                    btn.callback_data = cb_data[:64]  # limit: 1-64 bytes.
        return InlineKeyboardMarkup(ikb)

    def add(self, extra: Union[str, int]) -> InlineKeyboardMarkup:
        """Add extra Data to callback_data of every button

        Parameters:
        ----------
            - extra (`Union[str, int]`): Extra data e.g A `key` or `user_id`.

        Raises:
        ------
            `TypeError`

        Returns:
        -------
            `InlineKeyboardMarkup`: Modified markup
        """
        return self.__add__(extra)


class SearchResult:
    def __init__(
        self,
        key: str,
        text: str,
        image: str,
        buttons: InlineKeyboardMarkup,
    ) -> None:
        self.key = key
        self.buttons = Buttons(buttons.inline_keyboard)
        self.caption = text
        self.image_url = image

    def __repr__(self) -> str:
        out = self.__dict__.copy()
        out["buttons"] = (
            json.loads(str(btn)) if (btn := out.pop("buttons", None)) else None
        )
        return json.dumps(out, indent=4)

async def get_download_button(yt_id: str, user_id: int) -> SearchResult:
    buttons = [
        [
            InlineKeyboardButton(
                "⭐️ BEST - 📹 MP4",
                callback_data=f"yt_dl|{yt_id}|mp4|{user_id}|v",
            ),
        ]
    ]
    best_audio_btn = [
        [
            InlineKeyboardButton(
                "⭐️ BEST - 🎵 320Kbps - MP3",
                callback_data=f"yt_dl|{yt_id}|mp3|{user_id}|a",
            )
        ]
    ]
    params = {"no-playlist": True}
    try:
        ydl = YoutubeDL(params)
        vid_data = await extract_info(ydl, f"{YT_VID_URL}{yt_id}", download=False)
    except ExtractorError:
        vid_data = None
        buttons += best_audio_btn
    else:
        # ------------------------------------------------ #
        qual_dict = defaultdict(lambda: defaultdict(int))
        qual_list = ("1440p", "1080p", "720p", "480p", "360p", "240p", "144p")
        audio_dict: Dict[int, str] = {}
        # ------------------------------------------------ #
        for video in vid_data["formats"]:
            fr_note = video.get("format_note")
            fr_id = video.get("format_id")
            fr_size = video.get("filesize")
            if video.get("ext") == "mp4":
                for frmt_ in qual_list:
                    if fr_note in (frmt_, frmt_ + "60"):
                        qual_dict[frmt_][fr_id] = fr_size
            if video.get("acodec") != "none":
                bitrrate = video.get("abr")
                if bitrrate == (0 or "None"):
                    pass
                else:
                    audio_dict[
                        bitrrate
                    ] = f"🎵 {bitrrate}Kbps ({humanbytes(fr_size) or 'N/A'})"
        audio_dict = delete_none(audio_dict)
        video_btns: List[InlineKeyboardButton] = []
        for frmt in qual_list:
            frmt_dict = qual_dict[frmt]
            if len(frmt_dict) != 0:
                frmt_id = sorted(list(frmt_dict))[-1]
                frmt_size = humanbytes(frmt_dict.get(frmt_id)) or "N/A"
                video_btns.append(
                    InlineKeyboardButton(
                        f"📹 {frmt} ({frmt_size})",
                        callback_data=f"yt_dl|{yt_id}|{frmt_id}+140|{user_id}|v",
                    )
                )
        buttons += sublists(video_btns, width=2)
        buttons += best_audio_btn
        buttons += sublists(
            list(
                map(
                    lambda x: InlineKeyboardButton(
                        audio_dict[x], callback_data=f"yt_dl|{yt_id}|{x}|{user_id}|a"
                    ),
                    sorted(audio_dict.keys(), reverse=True),
                )
            ),
            width=2,
        )

    return SearchResult(
        yt_id,
        (
            f"<a href={YT_VID_URL}{yt_id}>{vid_data.get('title')}</a>"
            if vid_data
            else ""
        ),
        vid_data.get("thumbnail")
        if vid_data
        else "https://s.clipartkey.com/mpngs/s/108-1089451_non-copyright-youtube-logo-copyright-free-youtube-logo.png",
        InlineKeyboardMarkup(buttons),
    )

def delete_none(_dict):
    """Delete None values recursively from all of the dictionaries, tuples, lists, sets"""
    if isinstance(_dict, dict):
        for key, value in list(_dict.items()):
            if isinstance(value, (list, dict, tuple, set)):
                _dict[key] = delete_none(value)
            elif value is None or key is None:
                del _dict[key]

    elif isinstance(_dict, (list, set, tuple)):
        _dict = type(_dict)(delete_none(item) for item in _dict if item is not None)

    return _dict