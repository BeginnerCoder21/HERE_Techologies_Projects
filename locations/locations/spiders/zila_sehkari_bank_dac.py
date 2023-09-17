import scrapy
from locations.categories import Code
import uuid
import re
from locations.items import GeojsonPointItem
import pycountry
import json

class ZilaSehkariBankSpider(scrapy.Spider):
    name = "zila_sehkari_bank_dac"
    brand_name = "Zila Sahkari Bank"
    spider_chain_id = "8151"
    spider_type = "chain"
    spider_categories = [Code.BANK.value]
    spider_countries = [pycountry.countries.lookup('ind').alpha_3]
    allowed_domains = ["zsblghaziabad.com"]
    start_urls = ["https://zsblghaziabad.com/branchATM.php"]


    def start_requests(self):
        url = self.start_urls[0]
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        }
        yield scrapy.Request(
            url=url,
            headers=headers,
            callback=self.parse
        )

    def parse(self, response):
        '''
        @url https://zsblghaziabad.com/branchATM.php
        @returns items 1 35
        @scrapes ref name addr_full city state country phone website email chain_id chain_name
        '''
        branches = response.xpath('//tr[@class="NormalText"]')

        for branch in branches:
            website= 'https://zsblghaziabad.com/'
            country='India'
            state='Uttar Pradesh'
            branch_name =  branch.xpath('td[1]/text()').get()
            district = branch.xpath('td[2]/text()').get()
            ifsc_code=branch.xpath('td[4]/text()').get()
            address_parts = branch.xpath('string(td[3])').get().strip()
            phone_number = branch.xpath('td[5]/text()').get()
            email_id=""
            if "Email:" in address_parts:
                address_parts, email_id = address_parts.split("Email:")
            address = " ".join(address_parts.split())
            branch_name_with_ifsc = branch_name + f" {ifsc_code}" if ifsc_code else branch_name
            address = f"{address} {branch_name_with_ifsc}"

            data = {
                'ref':uuid.uuid4().hex,
                'name': branch_name_with_ifsc,
                'addr_full':address,
                'city': district,
                'state': state,
                'country': country,
                'phone':phone_number,
                'website': website,
                'email': email_id,
                'chain_id':self.spider_chain_id,
                'chain_name':self.brand_name
            }
            yield GeojsonPointItem(**data)