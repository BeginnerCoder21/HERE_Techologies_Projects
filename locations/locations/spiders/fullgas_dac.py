import scrapy
import pycountry
from locations.items import GeojsonPointItem
from locations.categories import Code
from typing import List
import uuid
import re


class FullgasSpider(scrapy.Spider):
    name = 'fullgas_dac'
    brand_name = 'FULLGAS'
    spider_chain_name = 'FULLGAS'
    spider_chain_id = '33760'
    spider_type: str = 'chain'
    spider_categories = [Code.PETROL_GASOLINE_STATION.value]
    spider_countries = [pycountry.countries.lookup('mex').alpha_3]
    allowed_domains= 'fullgas.com.mx'
    start_urls = ['https://fullgas.com.mx/index.php/ubicaciones']

    def parse(self, response):
        '''
        @url https://fullgas.com.mx/index.php/ubicaciones
        @returns items 1 130
        @scrapes ref lat lon name addr_full street city postcode country phone website store_url opening_hours
        '''
        element_with_class = response.xpath('//div[@class="elementor-element elementor-element-20ad31f elementor-widget elementor-widget-toggle"]')
        tables_inside_class = element_with_class.xpath('.//table')
        for table in tables_inside_class:
            rows = table.xpath('.//tr')
            for row in rows:

                if row.xpath('./td/text()'):
                    station = row.xpath('./td[1]/text()').get()
                    email = 'facturacion@fullgas.com.mx'
                    phone = '(01) 800 999 0367'
                    country = 'México'
                    address = row.xpath('./td[2]/text()').get()

                    if address is not None:
                        address = address.strip()

                    if address:
                        postcode = address[-5:]
                        address_parts = address.split(',')
                        city = address_parts[-3:-2][0].lower().strip() if len(address_parts) >= 3 else ""

                    else:
                        postcode = None

                    if isinstance(address, str):
                        street_match = re.match(r'([^,]+)', address)
                        street = street_match.group(1) if street_match else None
                    else:
                        street = None

                    location = row.xpath('./td[3]/a/@href').get()
                    latitude = 0
                    longitude = 0

                    if location:
                        pattern = r'@(-?[0-9.]+),(-?[0-9.]+)'
                        match = re.search(pattern, location)
                        if match:
                            if match.group(1)[0] == '-':
                                latitude = match.group(1)[1:]
                                longitude = match.group(2)
                            else:
                                latitude = match.group(1)
                                longitude = match.group(2)
                    else:
                        location="https://fullgas.com.mx/index.php/ubicaciones"

                    data = {
                        'ref':uuid.uuid4().hex,
                        'lat': latitude,
                        'lon': longitude,
                        'name': station,
                        'addr_full':address,
                        'street': street,
                        'city': city,
                        'postcode':postcode,
                        'country': country,
                        'phone':"".join(re.findall(r'\d', phone)),
                        'website': "https://fullgas.com.mx",
                        'store_url':location,
                        'email': email,
                        'opening_hours': '24/7',
                        'chain_id':self.spider_chain_id,
                        'chain_name':self.brand_name,
                        'brand': self.brand_name
                    }
                    yield GeojsonPointItem(**data)
                    