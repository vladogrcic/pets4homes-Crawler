import json

import requests
import scrapy
from currency_converter import CurrencyConverter
from scrapy import Request
from scrapy.crawler import CrawlerProcess


class Pets4homesSpider(scrapy.Spider):
    name = 'pets4homes'
    allowed_domains = ['pets4homes.co.uk']
    currLink = 'https://api.exchangeratesapi.io/latest?base=GBP'
    start_urls = [
        # 'https://www.pets4homes.co.uk/sale/birds/canaries/',
        'https://www.pets4homes.co.uk/responsive_browse_pets.php?page=1&advert_type=1&pettype=birds&petbreed=canaries',
        # currLink
    ]
    currencyRate = json.loads(requests.get(currLink).content)

    def parse(self, response):
        page = response.css(
            'div.inner-div-search > div.paginate .inactive ::text').extract_first()
        items = response.css(
            'div.inner-div-search .col-xs-12.profilelisting')
        for item in items:
            url = item.css('h2.headline a::attr(href)').extract_first()
            price = int(
                float(item.css('div.listingprice ::text').extract_first()[1:]))
            c = CurrencyConverter()
            finPriceUSD = c.convert(price, 'GBP', 'USD')
            finPriceEUR = c.convert(price, 'GBP', 'EUR')
            mainItem = {
                'title': item.css('h2.headline a ::text').extract_first(),
                'posted': item.css('div.profile-listing-updated ::text').extract_first().replace(chr(160), ''),
                'price': '£'+str(price)+', $'+str(round(finPriceUSD, 2))+', €'+str(round(finPriceEUR, 2)),
                'page': page,
                'numOfItemsOnPage': len(items)
            }
            yield Request(url, self.parse_item, meta={'item': mainItem})
        # url = 'https://api.exchangeratesapi.io/latest'
        # yield Request(url, self.parse_data, priority=1)
        # if not self.next_pages:
        next_pages = response.css(
            'div.inner-div-search > div.paginate span.inactive + a::attr(href)').extract_first()
        if next_pages is not None:

            url = response.urljoin(next_pages)
            yield response.follow(url, callback=self.parse)

    def parse_item(self, response):
        out = response.meta['item']
        items = response.css(
            'div.inner-div10')
        for item in items:
            contactLinks = item.css(
                '.col-xs-12.contactbox > a::attr(href)').extract()

            i = 0
            while i < len(contactLinks):
                if "email-seller" in contactLinks[i]:
                    out['email'] = contactLinks[i]
                i += 1

            out['image'] = 'http:'+item.css(
                '.active.item.caro-image img::attr(src)').extract_first()
            out['phone'] = item.css(
                '.col-xs-12.contactbox > a .dsptl::text').extract_first()[::-1][1:]
            out['fullDescription'] = ' '.join(item.css(
                '.inner-div10 > .col-xs-12.col-sm-7.col-md-8.col-lg-8 > .row > .col-xs-12').css('h2:contains("Full Advert Details") + p::text').extract())

            keyAdvertFacts = item.css(
                '.inner-div10 > .col-xs-12.col-sm-7.col-md-8.col-lg-8 > .row > .col-xs-12').css('h2:contains("Key Advert Facts") + div.row')
            out['animalAge'] = ''.join(keyAdvertFacts.css(
                'div:contains("Pets Current Age : ") + div::text').extract())[:-3].replace(' old', '').split(', ')
            out['location'] = ''.join(keyAdvertFacts.css(
                'div:contains("Location : ") + div a::text').extract())

        return out


if __name__ == '__main__':
    open('canary/spiders/canary.json', 'w').close()
    process = CrawlerProcess({
        # 'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        # 'USER_AGENT': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0)',
        'FEED_FORMAT': 'json',
        'FEED_URI': 'canary/spiders/canary.json',
        'FEED_EXPORT_ENCODING': 'utf-8'
    })
    process.crawl(Pets4homesSpider)
    process.start()  # the script will block here until the crawling is finished
