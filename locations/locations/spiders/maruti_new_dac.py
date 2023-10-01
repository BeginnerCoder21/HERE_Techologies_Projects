import scrapy
import uuid
import re
import json
from bs4 import BeautifulSoup
from locations.items import GeojsonPointItem

class MarutiCitiesSpider(scrapy.Spider):
    name = "maruti_new_dac"
    start_urls = ["https://www.marutisuzuki.com/dealer-showrooms"]
    cities_url = "https://www.marutisuzuki.com/api/sitecore/QuickLinks/GetCitiesForDealers"

    def parse(self, response):
        # Extract state options
        state_select = response.css('#dealer-state')
        state_options = state_select.css('option')
        states = {option.attrib['value']: option.css('::text').get().strip() for option in state_options if option.attrib.get('value')}
        # print(states)
        for state_code, state_name in states.items():
            yield scrapy.FormRequest(
                url=self.cities_url,
                formdata={"stateCode": state_code},
                callback=self.parse_cities,
                meta={"state_name": state_name}
            )

    def parse_cities(self, response):
        state_name = response.meta["state_name"]
        cities_data = json.loads(response.body)
        cities = cities_data
        
        for city in cities:
            city_name = city['CityName'].lower()
            # dealer_url = f"https://app.mapmyindia.com/MarutiWebAPI/searchdata?city={city_name}&category={category}"
            formdata = {
                        'city': city_name,
                        'category': 'dealer'
                    }
            headers = {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Cookie': 'JSESSIONID=KAom9CwRyVddSRlaNK5G8klHczKY-GOFWd1u_z8V.geomarketing-web-prod'
                    }

            yield scrapy.FormRequest(
                        url="https://app.mapmyindia.com/MarutiWebAPI/getSearchData",
                        headers=headers,
                        formdata=formdata,
                        callback=self.parse_dealer_details,
                        meta={"state_name": state_name, "city_name": city_name}
                    )
    
    def parse_dealer_details(self, response):
        '''
        @url https://www.marutisuzuki.com/dealer-showrooms
        @returns items 1 3224
        @scrapes ref chain_id chain_name name city addr_full email phone lat lon website
        '''
        def extract_postcode(address):
            postcode_match = re.search(r'(\b\d{6}\b)', address)
            return postcode_match.group(1) if postcode_match else ''
        
        def extract_house_number(address):
            # Split the address by whitespace and take the first part as the house number
            parts = address.split()
            house_number = parts[0] if parts else ''
            
            # Check if the house number contains any numeric characters
            contains_numbers = any(char.isdigit() for char in house_number)
            return house_number, contains_numbers
        
        json_data = response.json()
        responseData = json_data.get('list', [])
        website="https://www.marutisuzuki.com"

        if not responseData:
            return
        
        for row in responseData:
            phone_numbers = [row.get(f'dealerphone{i}', '') for i in range(1, 6) if row.get(f'dealerphone{i}', '')]
            addr=row['dealeraddress']
            # postcode = extract_postcode(addr)
            store_url = row.get('website', '')
            if store_url and not store_url.startswith(('http://www.', 'http://')):
                row['website'] = f'http://www.{store_url}'

            data = {
                'ref': row['dealercode'],
                'name': row.get('dealername', ''),
                'addr_full': row.get('dealeraddress', ''),
                # 'postcode': postcode,
                'street': row.get('location', ''),
                'city': row.get('cityname', ''),
                'state': row.get('statename', ''),
                'country': 'India',
                'phone': phone_numbers,
                'website': website,
                'store_url': row.get('website'),
                'email': row.get('dealeremail') if 'dealeremail' in row and row['dealeremail'] else 'contact@maruti.co.in',
                'chain_id': '3354',
                'chain_name': 'MARUTI SUZUKI'
            }

            yield GeojsonPointItem(**data)