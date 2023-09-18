import scrapy
import re
import uuid
import json
import pycountry
from bs4 import BeautifulSoup
from locations.categories import Code
from locations.items import GeojsonPointItem

class Ginger55Spider(scrapy.Spider):
    name = "ginger_55_dac"
    brand_name = "Ginger Hotel"
    spider_chain_id = "23882"
    spider_type = "chain"
    spider_categories = [Code.HOTEL.value]
    spider_countries = [pycountry.countries.lookup('ind').alpha_3]
    allowed_domains = ["gingerhotels.com"]
    start_urls = ["https://www.gingerhotels.com/hotels"]


    def parse(self,response):
        '''
        @url ttps://www.gingerhotels.com/hotels
        @returns items 1 58
        @scrapes ref name addr_full website email phone lat lon
        '''
        soup = BeautifulSoup(response.text, 'html.parser')
        hotel_items = soup.find_all('div', class_='hotel-list-item')

        for item in hotel_items:
            hotel_name = item.find('div', class_='hotel-list-name').text
            data_link = item.find('div', class_='hotelemapdata')['data-link']

            hotel_address_div = item.find('div', class_='hotel-list-addess')
            hotel_address = hotel_address_div.find('a').text

            address_parts = hotel_address.split(', ')
            city = address_parts[-1].split('-')[0].strip() if '-' in address_parts[-1] else ''
            street=address_parts[0]+" "+address_parts[1]
            postcode = address_parts[-1].split('-')[1].strip() if '-' in address_parts[-1] else address_parts[-1].strip()
            
            phone_number = item.find('div', class_='hotel-list-number').a.text
            phone_number=re.sub(r'[-/ ]', '', phone_number)

            location_data = item.find('div', class_='hotelemapdata')
            if location_data and 'data-location' in location_data.attrs:
                latitude, longitude = location_data['data-location'].split(',')
                latitude = latitude.strip()
                longitude = longitude.strip()

            data = {
                'ref':uuid.uuid4().hex,
                'lat': latitude,
                'lon': longitude,
                'name': hotel_name,
                'addr_full':hotel_address,
                'street': street,
                'city': city,
                'postcode':postcode,
                'country': 'India',
                'phone':phone_number,
                'website': "https://www.gingerhotels.com",
                'store_url':data_link,
                'email': 'instabook@gingerhotels.com',
                'chain_id':self.spider_chain_id,
                'chain_name':self.brand_name
            }
            yield GeojsonPointItem(**data)
