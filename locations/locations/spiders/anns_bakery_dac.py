import scrapy
from bs4 import BeautifulSoup
import pycountry
from locations.items import GeojsonPointItem
from locations.categories import Code
from typing import List
import uuid
import re

class FullgasSpider(scrapy.Spider):
    name = 'ann_dac'
    brand_name = 'Ann\'s Bakery'
    spider_chain_name = 'Ann\'s Bakery'
    spider_chain_id = '32701'
    spider_type: str = 'chain'
    spider_categories = [Code.SPECIALTY_STORE.value]
    spider_countries = [pycountry.countries.lookup('ind').alpha_3]
    allowed_domains= 'www.annsindia.com'
    start_urls = ['http://www.annsindia.com/']

    visited_stores = set()
    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')

        sections = soup.select('.section.group')
        for section in sections:
            store_blocks = section.select('.col_4, .col_3, .col, .col_2, .col_6, .col_5')
            for block in store_blocks:
                store_name_element = block.select_one('.store_header a')
                store_name = store_name_element.text.strip() if store_name_element else None
                if store_name and store_name not in self.visited_stores:
                    district_element = block.find_previous('h3', class_='division_header')
                    district = district_element.text if district_element else None
                    address_element = block.select_one('.store_address')
                    address = address_element.text.strip() if address_element else None
                    full_address = f'{district}, {address}'
                    tel_links = block.select('a[href^="tel:"]')
                    opening_hours="09:00 - 19:00"
                    phone_numbers = [re.sub(r'\D', '', tel_link.get('href')) for tel_link in tel_links]
                    # postcode_match = re.search(r'\b(\d{6})\b', address)
                    if postcode_match:
                        postcode = postcode_match.group(1)  
                    else:
                        postcode=""
                    address_parts = address.split(',')
                    city = address_parts[-2].strip() if len(address_parts) >= 2 else None
                    street = address_parts[-3].strip() if len(address_parts) >= 2 else None
                    data = {
                                'ref':uuid.uuid4().hex,
                                'name': store_name,
                                'addr_full':full_address,
                                'street': street,
                                'city': city,
                                'state': 'Kerela',
                                # 'postcode':postcode,
                                'country': 'India',
                                'phone':phone_numbers,
                                'website': "http://www.annsindia.com/",
                                'opening_hours': opening_hours,
                                'chain_id':self.spider_chain_id,
                                'chain_name':self.brand_name,
                                'brand': self.brand_name
                            }
                    self.visited_stores.add(store_name)
                    yield GeojsonPointItem(**data)

