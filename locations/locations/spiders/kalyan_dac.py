import scrapy
from locations.categories import Code
import uuid
from locations.items import GeojsonPointItem
import pycountry
import json
import re

class KalyanSpider(scrapy.Spider):
    name = "kalyan_dac"
    brand_name = "Kalyan Jewellers"
    spider_chain_id = "32689"
    spider_type = "chain"
    spider_categories = [Code.SPECIALTY_STORE.value]
    spider_countries = [pycountry.countries.lookup('ind').alpha_3]
    allowed_domains = ["https://www.kalyanjewellers.net"]
    start_urls = ["https://www.kalyanjewellers.net/store-locator.php"]
    
    def parse_phone_numbers(self, store):
            phone_numbers = set()
            phone_elements = store.css("a::text").getall()
            for element in phone_elements:
                numbers = re.findall(r'\b\d{3,5}[-\s]\d{6,8}\b', element)
                cleaned_numbers = [re.sub(r'[^\d]', '', number) for number in numbers]
                phone_numbers.update(cleaned_numbers)
            if phone_numbers:
                return list(phone_numbers)
            else:
                 return ""    
            
    def parse(self, response):
        states = response.css(".do-locator-menu > li a[data-toggle='collapse'] + ul > li")
        
        for state in states:
            state_name = state.css("a::text").get()
            cities = state.css("ul.placeList > li")

            for city in cities:
                city_name = city.css("a::text").get()

                print(state_name,": ", city_name)
                store_info = city.css("ul.storeList li a")

                for store in store_info:
                    store_name = store.css("h6::text").get()
                    city_name = store.css("b::text").get()
                    address_parts = store.css("a::text").getall()
                    address = ' '.join([part.strip() for part in address_parts if part.strip()])
                    address = re.sub(r'[^\w\s]', ' ', address)
                    address = ' '.join(address.split())
                    
                    phone_numbers = self.parse_phone_numbers(store)
                    postcode_match = re.search(r'\b(\d{6})\b', address)
                    postcode = postcode_match.group(1) if postcode_match else None
                    email='info@kalyanjewellers.net'
                    latitude = store.css("a::attr(data-lat)").get()
                    longitude = store.css("a::attr(data-lng)").get()
                    state=state
                    website = "https://www.kalyanjewellers.net"

                    data = {
                        'ref': uuid.uuid4().hex,
                        'lat': latitude,
                        'lon': longitude,
                        'name': self.brand_name,
                        'addr_full': address,
                        'city': city_name,
                        'state': state_name,
                        'postcode': postcode,
                        'country': 'India',
                        'brand': self.brand_name,
                        'phone': phone_numbers,
                        'website': website,
                        'email': email,
                        'chain_id': '32689',
                        'chain_name': store_name
                    }
                    yield GeojsonPointItem(**data)


