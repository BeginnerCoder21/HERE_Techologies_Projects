import scrapy
import pycountry
from locations.items import GeojsonPointItem
from locations.categories import Code
import json
from bs4 import BeautifulSoup
import re
import geojson
import requests
import uuid

class MaharashtraNaturalgasSpider(scrapy.Spider):
    name = "maharashtra_natural_gas_dac"
    brand_name = "Maharashtra Natural Gas"
    spider_chain_id = "301855"
    spider_type = "chain"
    spider_categories = [Code.FUELING_STATION]
    spider_countries = [pycountry.countries.lookup('ind').alpha_3]
    allowed_domains = ["mngl.in"]
    #start_urls = ["https://mngl.in/cng/cylinders-filling-stations"]

    def start_requests(self):
        url = "https://mngl.in/cng/cylinders-filling-stations"
        headers = {
            'Cookie': 'XSRF-TOKEN=eyJpdiI6IllqekJuUzRpTERsMkROK1ZcL0g3VThBPT0iLCJ2YWx1ZSI6InM2NFRLT0c1amVrSE9FdUJZZjh2OXVudFhjUWhTSWdaaUhwSGFvUTlIc3hENlZCVkhVSmk0a3FJMkQyOW1mZ1pcL05ua1QxMTF1M0Z2VXVyUDhqdjJ0K2hCWUFTYzZucE93WGpuUXVFZXdWZmhrc2hXakIybHVCSnRVQUp1VEYrMCIsIm1hYyI6IjM2NWM2YzMwNTQ3MmQxZmVmNDBmMWE5NTc4NTcyN2Y4MjgxNzU4OTU3OTM2ZTU4OTdmNWQ5ZGFiMWE5M2EyYTgifQ%3D%3D; mngl_session=eyJpdiI6IlNvblZKXC9maHBCNTZmUm9hYXNQbzRBPT0iLCJ2YWx1ZSI6IjNWbXh5MzJuUDRZcTBJemJDOFJzcENyY3dTQnViRXJNeXVMZytERjVTWkxNM1lWWm43d0N3aGxjRVBvdEdiNDhYc3lKbUNITDNFbURza0JTdFRpQ3paWXhjakVYUVwvRGZlZUlQZjduSDk1OGFiXC9LZWFvc3BSUDdZWkhyb1gxNFAiLCJtYWMiOiI4NWZiYjk4MjIzODhkNmFkY2QzNDY4NGM1NWZmMTU1MmI5ZWQ0MDc0Njg5YmY5MzhhZmU1YmIwMWM1OGVlNDA4In0%3D',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        }
        yield scrapy.Request(
            url=url,
            headers=headers,
            callback=self.parse
        )

    def parse(self, response):
        '''
        @url https://mngl.in/cng/cylinders-filling-stations
        @returns items 1 99
        @scrapes ref chain_id chain_name name city addr_full email phone lat lon website
        '''

        
        def coordinate(angle):
            deg, minutes, seconds, direction = re.split('[°\'"]', angle)
            return round((float(deg) + float(minutes)/60 + float(seconds)/(60*60)) * (-1 if direction in ['W', 'S'] else 1), 6)

        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.find("table", {"class": "table table-bordered table-striped"})
        rows = rows.find_all("tr")

        for row in rows[1:]: 
            columns = row.find_all("td")
            station_name = columns[1].text.strip()
            city = columns[2].text.strip()
            cluster = columns[4].text.strip()
            address=columns[2].text + ' ' + columns[3].text + ' ' + cluster
            address=address.strip()
            website= 'https://mngl.in/'
            phone_number = response.xpath('//div[@class="col-md-8 pr-3 pr-sm-0 m-0"]/ul/li[contains(i/@class, "fa-phone")]/a/text()').get().replace(' ', '')
            email = response.xpath('//html/body/div[1]/footer/div/div/div[1]/div[5]/div[6]/p/a/text()').get()
            if "°" in columns[5].find("a").get('href'):
                lon = coordinate(columns[5].find("a").get('href').split('/')[5].split(' ')[1].replace('\\', ''))
                lat = coordinate(columns[5].find("a").get('href').split('/')[5].split(' ')[0].replace('\\', ''))
            else:
                lon = columns[5].find("a").get('href').split('/')[5].split(',')[1]
                lat = columns[5].find("a").get('href').split('/')[5].split(',')[0]

            data = {
                    'ref': uuid.uuid4().hex,
                    'chain_id': self.spider_chain_id,
                    'chain_name': self.brand_name,
                    'name': station_name,
                    'email': email,
                    'city': city,
                    'addr_full': address,
                    'phone': phone_number,
                    'lat': lat,
                    'lon': lon,
                    'website': website
            }

            yield GeojsonPointItem(**data)
                
                                   