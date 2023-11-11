import requests

from pyrogram.types import InlineQueryResultPhoto

from whiterkang import Config

class PexelsImagesAPI:
    def __init__(self):
        self.pexels_results = []
        self.pexels_api_key = Config.PEXELS_API_KEY
        self.pexels_url = "https://api.pexels.com/v1/search"

    def pexels_image(self, query: str, per_page: int):
        headers = {
            "Authorization": self.pexels_api_key
        }
        params = {
            "query": query,
            "per_page": per_page,
        }
        
        res = requests.get(self.pexels_url, headers=headers, params=params)
        data = res.json()

        images = []
        for image in data["photos"]:
            images.append(image["src"]["large"])
        return images

    def pexels_results_photo(self, query: str, per_page: int):
        search_results = self.pexels_image(query, per_page)
        for i, image_url in enumerate(search_results):
            self.pexels_results.append(
                InlineQueryResultPhoto(
                    photo_url=image_url,
                )
            )
        return self.pexels_results
        
