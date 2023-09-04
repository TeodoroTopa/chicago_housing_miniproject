import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy import Selector
import pandas as pd
import numpy as np
import requests

class ApartmentSpider(scrapy.Spider):

    name = 'ApartmentSpider'

    custom_settings = {
        'USER_AGENT' : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) \
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
    }

    def start_requests(  self  ):
        for url in master_urls:
            yield scrapy.Request(url = url[0], callback = self.parse)


    def parseListings( self, listings, neighborhood, response):
        for apt in listings:

            listing_classes = apt.xpath("./article/@class").extract()[0]
            listing_class = 0

            address = apt.xpath("./article/@data-streetaddress").extract()[0]
            property_link = apt.xpath("./article/@data-url").extract()[0]
            hood = neighborhood

            if("placard-option-gold" in listing_classes) :
                listing_class = 1
                cost = apt.xpath(".//p[@class='property-pricing']/text()").extract()[0]
                name = apt.xpath(".//p[@class='property-for-rent']/text()").extract()[0]
                beds = apt.xpath(".//p[@class='property-beds']/text()").extract()[0]
                zipcode = apt.xpath(".//div[@class='property-address js-url']/text()").extract()[0]

            elif("placard-option-platinum" in listing_classes) :
                listing_class = 4
                cost = apt.xpath(".//p[@class='property-pricing']/text()").extract()[0]
                name = apt.xpath(".//a[@class='property-link']/@aria-label").extract()[0]
                beds = apt.xpath(".//p[@class='property-beds']/text()").extract()[0]
                zipcode = apt.xpath(".//div[@class='property-address js-url']/text()").extract()[0]

            elif("placard-option-premium" in listing_classes) :
                listing_class = 2
                cost = apt.xpath(".//span[@class='property-rents']/text()").extract()[0]
                name = apt.xpath(".//a[@class='property-link']/@aria-label").extract()[0]
                beds = apt.xpath(".//span[@class='property-beds']/text()").extract()[0]
                zipcode = apt.xpath(".//p[@class='property-address js-url']/text()").extract()[-1]

            else:
                listing_class = 3
                cost = apt.xpath(".//div[@class='price-range']/text()").extract()[0]
                name = apt.xpath(".//div[@class='property-title']/@title").extract()[0]
                beds = apt.xpath(".//div[@class='bed-range']/text()").extract()[0]
                zipcode = apt.xpath(".//div[@class='property-address js-url']/text()").extract()[0]

            print("HERE WE GO", property_link)
            response.follow(url = property_link, callback=self.parse_baths_sqft)
            #bath_and_sqft = self.parseListingPage(property_link)
            info_tuple = (listing_class, cost, name, address, beds, hood, zipcode, property_link)
            master_listings.append(info_tuple)

    def parse_baths_sqft( self, response):

        itemlist = response.xpath(".//div[@class='priceBedRangeInfoInnerContainer']").getAll()
        print("\n")
        print("---------------------------------------------")
        print("---------------------------------------------")
        print("---------------------------------------------")
        print(itemlist)
        print("---------------------------------------------")
        print("---------------------------------------------")
        print("---------------------------------------------")
        print("\n")
        #baths = itemlist[2].xpath()
        #sqft = property_link.xpath()



        #return(baths, sqft)


    def parse(  self, response):

        urls = []

        pagestring = response.xpath("//span[@class='pageRange']/text()").extract()[0]
        pages = int(pagestring.split(' ')[-1])


        for page in range(1,pages+1):
            urls.append(response.request.url + str(page) + "/")

        for url in urls:
            yield scrapy.Request(url = url, callback = self.parsePostingPage)


    def parsePostingPage( self, response):
        listings = response.xpath("//div[@id='placardContainer']//ul//li[@class='mortar-wrapper']")
        if ("wicker-park" in response.request.url) : neighborhood = "Wicker Park"
        elif ("west-town" in response.request.url) : neighborhood = "West Town"
        elif ("bucktown" in response.request.url) : neighborhood = "Bucktown"
        elif ("logan-square" in response.request.url) : neighborhood = "Logan Square"
        elif ("ukrainian-village" in response.request.url) : neighborhood = "Ukrainian Village"
        else: neighborhood = "UNKNOWN"
        self.parseListings(listings, neighborhood, response)


master_urls = [("https://www.apartments.com/wicker-park-chicago-il/", "Wicker Park"),
("https://www.apartments.com/west-town-chicago-il/", "West Town"),
("https://www.apartments.com/bucktown-chicago-il/", "Bucktown"),
("https://www.apartments.com/logan-square-chicago-il/", "Logan Square"),
("https://www.apartments.com/ukrainian-village-chicago-il/", "Ukrainian Village")]

master_listings = []

process = CrawlerProcess()
process.crawl(ApartmentSpider)
process.start()

df = pd.DataFrame(master_listings, columns= ['listing_class', 'cost', 'name', 'address', 'beds', 'neighborhood', 'zipcode', 'property_link'])
df.to_csv('scraped_apartment_results1129.csv', index= False)
