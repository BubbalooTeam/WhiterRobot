import requests
import json
import uuid
import asyncio

from httpx import AsyncClient
from bs4 import BeautifulSoup
from fake_headers import Headers

from whiterkang import db

proxys = {
    "PROXIES":
    [
        "https://8.208.90.243:9992",
        "https://8.208.89.32:8081",
        "https://8.208.90.243:2020",
        "http://198.11.175.180:6969",
        "http://191.240.153.165:8080",
        "http://47.254.47.61:18081",
        "http://50.223.38.98:80",
        "https://8.213.137.155:8084"
    ]
    
}

DB_ = db["REQUESTS_TEXT"]

async def getDataFromUrl(url):
    find_db = await DB_.find_one({"url": url})
    if find_db:
        return find_db["text"]
    else:    
        header = Headers(
            browser="chrome",
            os="win",
            headers=True
        )
        res = requests.get(url, headers=header.generate())
        if res.status_code != 200:
            for proxy in proxys["PROXIES"]:
                response = requests.get(url, headers=header.generate(), proxies={'http': proxy})
                if response.status_code == 200:
                    await DB_.update_one({"url": url}, {"$set": {"text": response.text}}, upsert=True)
                    break
            return response.text
        else:  # noqa: RET505
            await DB_.update_one({"url": url}, {"$set": {"text": res.text}}, upsert=True)
            return res.text
    
async def search_device(searchValue):
    url = f"https://gsmarena.com/results.php3?sQuickSearch=yes&sName={searchValue}"
    html = await getDataFromUrl(url)

    soup = BeautifulSoup(html, 'html.parser')

    json = []

    devices = soup.select('.makers li')

    for i, el in enumerate(devices):
        imgBlock = el.find('img')

        json.append({
            'id': el.find('a')['href'].replace('.php', ''),
            'name': el.find('span').text.replace('\n', '').replace('\r', '').replace('\t', ''),
            'img': imgBlock['src'],
            'description': imgBlock['title'],
        })

    return json

async def get_device(device):
    html = await getDataFromUrl(f'https://www.gsmarena.com/{device}.php')
    soup = BeautifulSoup(html, 'html.parser')
    display_size_base = soup.find('span', {'data-spec': 'displaysize-hl'})
    display_size = display_size_base.get_text() if display_size_base else "N/A"
    display_res_base = soup.find('div', {'data-spec': 'displayres-hl'})
    display_res = display_res_base.get_text() if display_res_base else "N/A"
    camera_pixels_base = soup.find(class_='accent-camera')
    camera_pixels = camera_pixels_base.get_text() if camera_pixels_base else "N/A"
    video_pixels_base = soup.find('div', {'data-spec': 'videopixels-hl'})
    video_pixels = video_pixels_base.get_text() if video_pixels_base else "N/A"
    ram_size_base = soup.find(class_='accent-expansion')
    ram_size = ram_size_base.get_text() if ram_size_base else "N/A"
    chipset_base = soup.find('div', {'data-spec': 'chipset-hl'})
    chipset = chipset_base.get_text() if chipset_base else "N/A"
    battery_size_base = soup.find(class_='accent-battery')
    battery_size = battery_size_base.get_text() if battery_size_base else "N/A"
    battery_type_base = soup.find('div', {'data-spec': 'battype-hl'})
    battery_type = battery_type_base.get_text() if battery_type_base else "N/A"
    quick_spec = [
        {'name': 'Display size', 'value': display_size},
        {'name': 'Display resolution', 'value': display_res},
        {'name': 'Camera pixels', 'value': camera_pixels},
        {'name': 'Video pixels', 'value': video_pixels},
        {'name': 'RAM size', 'value': ram_size},
        {'name': 'Chipset', 'value': chipset},
        {'name': 'Battery size', 'value': battery_size},
        {'name': 'Battery type', 'value': battery_type},
    ]
    name_base = soup.find(class_='specs-phone-name-title')
    name = name_base.get_text() if name_base else "N/A"
    img = soup.find('div', class_='specs-photo-main').find('img').get('src')
    spec_nodes = soup.find_all('table')
    detail_spec = []
    for el in spec_nodes:
        spec_list = []
        category_base = el.find('th')
        category = category_base.get_text() if category_base else "N/A"
        spec_n = el.find_all('tr')
        for ele in spec_n:
            ttl = ele.find('td', class_='ttl')
            nfo = ele.find('td', class_='nfo')
            if ttl and nfo:
                spec_list.append({
                    'name': ttl.get_text(),
                    'value': nfo.get_text(),
                })
        if category:
            detail_spec.append({
                'category': category,
                'specifications': spec_list,
            })
    return {
        'name': name,
        'img': img,
        'detailSpec': detail_spec,
        'quickSpec': quick_spec 
    }
