import requests
import logging

from whiterkang import Config, db

DB_ = db["DEVICES"]

async def getDataFromUrl(url):
    datadb = await DB_.find_one({"url": url})
    if datadb:
        logging.info("Device Database Finded: {}".format(url))
        return datadb["result"]
    else:
        res = requests.get(url).json()
        await DB_.update_one({"url": url}, {"$set": {"result": res}})
        logging.info("Requested Device: {}".format(url))
        return res

async def search_device(searchValue):
    url = "{}/search?value={}".format(Config.GSMARENA_API, searchValue)
    res = await getDataFromUrl(url)
    return res
    

async def get_device(device):
    url = "{}/getdevice?value={}".format(Config.GSMARENA_API, device)
    res = await getDataFromUrl(url)
    return res