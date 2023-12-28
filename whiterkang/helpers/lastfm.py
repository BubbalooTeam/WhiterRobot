# WhiterRobot
# Copyright (C) 2023 BubbalooTeam
#
# This file is based of < https://github.com/KuuhakuTeam/YuunaRobot/ >
# PLease read the MIT License Agreement in 
# <https://github.com/BubbalooTeam/WhiterRobot/tree/main/LICENCE>.

import logging
from uuid import uuid4

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

class Fonts:
    ARIAL = 'whiterkang/fonts/arial-unicode-ms.ttf'
    OPEN_BOLD = 'whiterkang/fonts/OpenSans-Bold.ttf'
    OPEN_SANS = 'whiterkang/fonts/OpenSans-Regular.ttf'
    POPPINS = 'whiterkang/fonts/Poppins-SemiBold.ttf'


def truncate(text, font, limit):
    edited = True if font.getlength(text) > limit else False
    while font.getlength(text) > limit:
        text = text[:-1]
    if edited:
        return(text.strip() + '..')
    else:
        return(text.strip())


def checkUnicode(text):
    return text == str(text.encode('utf-8'))[2:-1]

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

def draw_scrobble(
    img_: str,
    pfp: str,
    song_name: str,
    artist_name: str,
    user_lastfm: str,
    listening: str,
    loved: bool):
        # background object
        canvas = Image.new("RGB", (600, 250), (18, 18, 18))
        draw = ImageDraw.Draw(canvas)

        # album art
        try:
            art_ori = Image.open(img_).convert("RGB")
            art = Image.open(img_).convert("RGB")
            enhancer = ImageEnhance.Brightness(art)
            im_ = enhancer.enhance(0.7)
            blur = im_.filter(ImageFilter.GaussianBlur(20))
            blur_ = blur.resize((600, 600))
            canvas.paste(blur_, (0, -250))

            # original art
            art_ori = art_ori.resize((200, 200), Image.LANCZOS)
            canvas.paste(art_ori, (25, 25))
        except Exception as ex:
            logging.error(ex)

        # profile pic
        o_pfp = Image.open(pfp).convert("RGB")
        o_pfp = o_pfp.resize((52, 52), Image.LANCZOS)
        canvas.paste(o_pfp, (523, 25))

        # set font sizes
        open_sans = ImageFont.truetype(Fonts.OPEN_SANS, 21)

        # open_bold = ImageFont.truetype(Fonts.OPEN_BOLD, 23)
        poppins = ImageFont.truetype(Fonts.POPPINS, 25)
        arial = ImageFont.truetype(Fonts.ARIAL, 25)
        arial23 = ImageFont.truetype(Fonts.ARIAL, 21)

        # assign fonts
        songfont = poppins if checkUnicode(song_name) else arial
        artistfont = open_sans if checkUnicode(artist_name) else arial23

        # draw text on canvas
        white = '#ffffff'
        draw.text((248, 18), truncate(user_lastfm, poppins, 250),
                fill=white, font=poppins)
        draw.text((248, 53), listening,
                fill=white, font=open_sans)
        draw.text((248, 115), truncate(song_name, songfont, 315),
                fill=white, font=songfont)
        draw.text((248, 150), truncate(artist_name, artistfont, 315),
                fill=white, font=artistfont)

        # draw heart
        if loved:
            lov_ = Image.open("whiterkang/resources/heart.png", 'r')
            leve = lov_.resize((25, 25), Image.LANCZOS)
            canvas.paste(leve, (248, 190), mask=leve)
            draw.text((278, 187), truncate("loved", artistfont, 315),
                    fill=white, font=artistfont)

        duration = 15
        current_time = 5
        bar_color = (0, 0, 0) # black
        progress_color = (255, 255, 255) # white
        bar_width = 300

        draw.rectangle((248, 220, 248 + bar_width, 240), fill=bar_color, outline=None, width=0, joint='curve')
        progress_width = round(bar_width * current_time / duration)
        draw.rectangle((248, 220, 248 + progress_width, 240), fill=progress_color, outline=None, width=0, joint='curve')
        
        current_time_str = f"{current_time // 60:02d}:{current_time % 60:02d}"
        duration_str = f"{duration // 60:02d}:{duration % 60:02d}"

        text_font = open_sans if checkUnicode(current_time_str + " / " + duration_str) else arial23

        draw.text((248, 245), current_time_str + " / " + duration_str, fill=white, font=text_font)

        # return canvas
        image = BytesIO()
        final_img = str(uuid4()) + ".jpg"
        canvas.save(final_img, format="jpeg")
        image.seek(0)
        return final_img
