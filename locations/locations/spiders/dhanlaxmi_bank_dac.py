import scrapy
import pycountry
from locations.items import GeojsonPointItem
from locations.categories import Code
from typing import List
import re


class DhanlaxmiBankIndOffice(scrapy.Spider):
    name = 'dhanlaxmi_bank_dac'
    brand_name = "Dhanlaxmi Bank"
    spider_type= 'chain'
    spider_chain_id = 2508
    spider_categories= [Code.BANK.value, Code.ATM.value]
    spider_countries = [pycountry.countries.lookup('ind').alpha_3]
    allowed_domains= ['dhanbank.com']
    start_urls = ['https://www.dhanbank.com/branch-locator/']

    def start_requests(self):
        url = "https://www.dhanbank.com/api/states/"

        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53'}

        yield scrapy.FormRequest(
            url=url,
            headers=header,
            method='GET',
            callback = self.parse_states
        )

    def parse_states(self, response):
        responseData = response.json()
        url="https://www.dhanbank.com/api/cities/?state="
        
        states_data = []
        for state in responseData['data']:
            for value in state.values():
                states_data.append(value)

        for state in states_data:
            yield scrapy.FormRequest(
                url=url+state.replace(' ', '%20'),
                method='GET',
                cb_kwargs=dict(state=state),
                callback=self.parse_cities
            )
    
    def parse_cities(self, response, state):
        responseData = response.json()
        cities = []
        for city in responseData['data']:
            for value in city.values():
                cities.append(value)

        for city in cities:
            yield scrapy.FormRequest(
                url=f"https://www.dhanbank.com/api/ab/?state={state.replace(' ', '%20')}&city={city.replace(' ', '%20')}",
                method='GET',
                callback=self.parse
            )

    def parse_coordinates(self, val):
        if "”" in val:
            deg, minutes, seconds = map(float, re.split('[°’”]', val.replace(" ", "")))
            coord = round((deg + minutes/60 + seconds/(60*60)), 6)
        elif "’" in val:
            deg, minutes, sec = map(float, re.split('[°’]', val.replace(" ", "")))
            coord = round((deg + minutes/60 + sec/(60*60)), 6)
        else:
            coord = float(val.replace(" ", ""))
        return coord

    def parse_address(self, row):
        address = ' '.join(row[key] for key in ['address1', 'address2', 'address3', 'address4', 'address5'] if row[key])
        postcode = row.get('pincode', '')
        address += postcode.replace(" ", "") if postcode else ''
        return address
    
    def extract_street(self, row):
        street_parts = [row.get(key, '') for key in ['address1', 'address2', 'address3']]
        street = ' '.join(part for part in street_parts if part)
        return street
    
    def parse(self, response):
        '''
        @url https://www.dhanbank.com/branch-locator/
        @returns items 1 530
        @scrapes ref country street city state name addr_full website email phone postcode lat lon chain_id chain_name
        '''
        responseData = response.json()
        for row in responseData['atmsAndBranches']:
            std_code = row.get('std_code', '')
            phone = row.get('phone', '')
            phone_numbers = re.findall(r'\d{2,}', phone) if phone else []
            if std_code:
                phone_with_std = [f"{std_code}{number}" for number in phone_numbers]
            else:
                phone_with_std = phone_numbers

            phone_str = ', '.join(phone_with_std) if phone_with_std else '04442413000'

            ifsc_code = row.get('ifsc_code', '')
            address = self.parse_address(row)
            if ifsc_code:
                address = f"{address}, {ifsc_code}"
            else:
                address = address 
            data = {
                'ref': row['id'],
                'country': 'India',
                'street': self.extract_street(row),
                'city': row['city'],
                'state': row['state'],
                'name': row['name'],
                'addr_full': address,
                'website': 'https://www.dhanbank.com/',
                'phone': phone_str,
                'postcode': row['pincode'],
                'email': row['email'] if row['email'] and row['email'] != "" else "customercare@dhanbank.co.in",
                'lat': self.parse_coordinates(row['latitude']),
                'lon': self.parse_coordinates(row['longitude']),
                'chain_id':self.spider_chain_id,
                'chain_name':self.brand_name
            }

            yield GeojsonPointItem(**data)