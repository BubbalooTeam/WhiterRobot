import asyncio
import logging

from whiterkang import WhiterX, db

DB_DEVICES = db["DEVICES"]

async def find_device(uid: int, device_id: str): 
    try:
        devices = await DB_DEVICES.find_one({"user_id": uid, "device_id": device_id})
        if devices:
            link = devices["link"]
            img = devices["img"]
            description = devices["description"]
        else:
            link = "N/A"
            img = "https://telegra.ph/file/55e52e064767ad9c1a6b7.jpg"
            description = "N/A"
        return link, img, description
    except Exception as e:
        return logging.error(f"An error occurred: {e}")

async def add_device(uid: int, device_id: str, link: str, img: str, description: str):
    try:
        await DB_DEVICES.insert_one({"user_id": uid, 
                                     "device_id": device_id, 
                                     "link": link, 
                                     "img": img, 
                                     "description": description
                                    }
                                   )
        
        devices = await DB_DEVICES.find_one({"user_id": uid, "device_id": device_id})

        if devices:
            logging.info(f"Saved a smartphone id: {device_id}")
        else:
            logging.error("An error occurred in save basic infos devices [id/link/img/description]")
    except Exception as e:
        return logging.error(f"An error occurred: {e}")

async def del_device(uid: str):
    try:
        await DB_DEVICES.delete_many({"user_id": uid})
    except Exception as e:
        return logging.error(f"An error occurred: {e}")