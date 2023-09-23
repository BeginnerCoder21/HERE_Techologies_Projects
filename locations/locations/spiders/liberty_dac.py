import scrapy
from locations.categories import Code
import uuid
from datetime import datetime as datetime
from locations.items import GeojsonPointItem
import pycountry
import json
import re
class LibertyShoesSpider(scrapy.Spider):
    name = "liberty_dac"
    brand_name = "Liberty"
    spider_chain_id = "4792"
    spider_type = "chain"
    spider_categories = [Code.CLOTHING_AND_ACCESSORIES.value]
    spider_countries = [pycountry.countries.lookup('ind').alpha_3]
    allowed_domains = ["libertyshoes.com"]
    start_urls = ["https://www.libertyshoes.com/ajax-query-pointer/"]

    def start_requests(self):
        url = self.start_urls[0]
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        }
        yield scrapy.Request(
            url=url,
            headers=headers,
            method='POST',
            callback=self.parse
        )

    def parse(self, response):
        '''
        @url https://www.libertyshoes.com/store-locator/
        @returns items 1 496
        @scrapes ref lat lon name addr_full postcode street city country brand phone website email opening_hours chain_id chain_name
        '''
        def convert_to_24_hour(time_str):
            time_parts = re.findall(r'(\d{1,2})[:.](\d{1,2})\s*([APMapm]{2})', time_str)

            if time_parts:
                opening_hour, opening_minute, opening_meridiem = time_parts[0]
                closing_hour, closing_minute, closing_meridiem = time_parts[-1]

                if opening_meridiem.upper() == 'PM' and opening_hour != '12':
                    opening_hour = str(int(opening_hour) + 12)

                if closing_meridiem.upper() == 'PM' and closing_hour != '12':
                    closing_hour = str(int(closing_hour) + 12)

                opening_time_str = f"{opening_hour.zfill(2)}:{opening_minute}"
                closing_time_str = f"{closing_hour.zfill(2)}:{closing_minute}"

                return opening_time_str, closing_time_str
            else:
                return " "," "
        
        def extract_postcode(addr_full):
            postcode_pattern = r'\b\d{6}\b'
            matches = re.findall(postcode_pattern, addr_full)
            return matches[0] if matches else ''
        
        json_data = re.search(r'\[.*\]', response.text).group()
        store_data_list = json.loads(json_data)
    
        for store in store_data_list:
            description = store.get('description') or ''
            description = re.sub(r'\n', '', description)
            address_parts = description.split(',')
            street = address_parts[0] if len(address_parts) > 0 else ''
            postcode = extract_postcode(description)

            store_time = store.get('store_time', '')
            if ' to ' in store_time:
                opening_time, closing_time = store_time.split(' to ')
            else:
                opening_time = closing_time = store_time
            opening_time_24hr, closing_time_24hr = convert_to_24_hour(opening_time), convert_to_24_hour(closing_time)
            opening_time_24hr,closing_time_24hr=list(set(opening_time_24hr)),list(set(closing_time_24hr))
            opening_time_24hr,closing_time_24hr=opening_time_24hr[0], closing_time_24hr[0]
            opening_hours = f"Mo-Su {opening_time_24hr}-{closing_time_24hr}"
            data = {
                        'ref': uuid.uuid4().hex,
                        'lat': store.get('lat', ''),
                        'lon': store.get('lng', ''),
                        'name': store.get('format', ''),
                        'addr_full': store.get('description', ''),
                        'postcode':postcode,
                        'street': street,
                        'city': store.get('city', ''),
                        'country': 'India',
                        'brand': self.brand_name,
                        'phone': store.get('phone_no', ''),
                        'website': 'https://www.libertyshoes.com',
                        'email': 'lsocare@libertyshoes.com',
                        'opening_hours':opening_hours,
                        'chain_id':self.spider_chain_id,
                        'chain_name':self.brand_name
                    }
            yield GeojsonPointItem(**data)