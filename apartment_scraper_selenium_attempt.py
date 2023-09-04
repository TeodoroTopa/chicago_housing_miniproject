import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy import Selector
import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
import requests

class ApartmentSpider(scrapy.Spider):
    
    name = 'ApartmentSpider'

    custom_settings = {
        'USER_AGENT' : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) \
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
    }
    
    def start_requests(  self  ):
        for url in master_urls:
            driver.get(url)
            yield scrapy.Request(url = url, callback = self.parse)
            
    
    def parseListings( self, listings ):
        listings_data = []
        for apt in listings:
            listing_classes = apt.xpath("./article/@class").extract()[0]
            listing_class = 3
            address = apt.xpath("./article/@data-streetaddress").extract()[0]
            property_link = apt.xpath("./article/@data-url").extract()[0] 
            
            if("placard-option-gold" in listing_classes) :
                listing_class = 1
                cost = apt.xpath(".//p[@class='property-pricing']/text()").extract()[0]
                name = apt.xpath(".//p[@class='property-for-rent']/text()").extract()[0]
                beds = apt.xpath(".//p[@class='property-beds']/text()").extract()[0]               

            elif("placard-option-premium" in listing_classes) : 
                listing_class = 2
                cost = apt.xpath(".//span[@class='property-rents']/text()").extract()[0]
                name = apt.xpath(".//a[@class='property-link']/@aria-label").extract()[0]
                beds = apt.xpath(".//span[@class='property-beds']/text()").extract()[0]

            else:
                cost = apt.xpath(".//div[@class='price-range']/text()").extract()
                name = apt.xpath(".//div[@class='property-title']/@title").extract()[0]
                beds = apt.xpath(".//div[@class='bed-range']/text()").extract()[0]
            
            info_tuple = (listing_class, cost, name, address, beds, property_link)
            listings_data.append(info_tuple)

        return(listings_data)

    def parse(  self, response  ):

        #selenium webdriver for next button
        complete_data = []

        pages= len(response.xpath("//nav[@id='paging']//ol//li"))
        print("pages", pages)

        for page in range(1,pages):
            print("\n\nPAGENUM \n\n", page)
            next_page = page + 1

            listings = response.xpath("//div[@id='placardContainer']//ul//li[@class='mortar-wrapper']")
            listings_data = self.parseListings(listings)
            print(listings_data)

            complete_data.append(listings_data)

            if next_page <= pages:
                print("\n\n\nCLICKING\n\n\n")
                driver.find_element(By.CSS_SELECTOR, "a[data-page='" + str(next_page) +  "']").click()
                print("\n\n\nCLICKED\n\n\n")
            else:
                print("\n\nBREAKING\n\n")
                break
            


driver = webdriver.Chrome("C:\\Users\\Topam\\Documents\\chromedriver_win32\\chromedriver.exe")


master_urls = ["https://www.apartments.com/wicker-park-chicago-il/2-bedrooms-under-1800/"]

process = CrawlerProcess()
process.crawl(ApartmentSpider)
process.start()