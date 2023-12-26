import requests
import logging

from whiterkang import Config, db

DB_ = db["DEVICES"]

async def getDataFromUrl(url):
    datadb = await DB_.find_one({"url": url})
    if datadb:
        return datadb["result"]
    else:
        res = requests.get(url).json()
        await DB_.update_one({"url": url}, {"$set": {"result": res}}, upsert=True)
        return res

async def search_device(searchValue):
    url = "{}/search?value={}".format(Config.GSMARENA_API, searchValue)
    res = await getDataFromUrl(url)
    return res
    

async def get_device(device):
    url = "{}/getdevice?value={}".format(Config.GSMARENA_API, device)
    res = await getDataFromUrl(url)
    return res

async def add_inf_device(device_id: str, link: str, img: str, description: str):
    try:
        await DB_.update_one({"device_id": device_id}, {"$set": {"link": link, "img": img, "description": description}}, upsert=True)
    except Exception as e:
        return logging.error(f"An error occurred: {e}")

async def find_inf_device(device_id: str):
    try:
        infos = await DB_.find_one({"device_id": device_id})
        if infos:
            link = infos["link"]
            img = infos["img"]
            description = infos["description"]
        else:
            link = "N/A"
            img = "https://telegra.ph/file/55e52e064767ad9c1a6b7.jpg"
            description = "N/A"
        return link, img, description
    except Exception as e:
        return logging.error(f"An error occurred: {e}")
    
async def del_inf_device(device_id: str):
    try:
        await DB_.delete_many({"device_id": device_id})
    except Exception as e:
        return logging.error(f"An error occurred: {e}")