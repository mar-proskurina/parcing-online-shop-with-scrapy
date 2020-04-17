# -*- coding: utf-8 -*-
import numpy as np
import scrapy
import re
import requests


class SportSpider(scrapy.Spider):


    custom_settings = {'FEED_URI': 'results/sport.csv'}

    name = 'sport'

    # Составляем корректный список страниц.
    allowed_domains = ['sportmaster.ru/']
    first_page = ['https://www.sportmaster.ru/catalog/vidy_sporta_/velosport/velosipedy/?f-age=age1_vzroslye']
    all_others = ['https://www.sportmaster.ru/catalog/vidy_sporta_/velosport/velosipedy/?f-age=age1_vzroslye&page=' + str(x) for x in range(2, 9)]

    # Вставлем на 1 меcто (0 индекс) нашу первую страницу и все остальные далее.
    start_urls = first_page + all_others

    def refine(self, string, field):
        compiled = re.compile('<.*?>')
        clean = re.sub(compiled, '|', string)
        clean = clean.strip('').replace('\t','').replace('\n', '')
        amount = clean.split('|')[field]
        return amount

    def parse(self, response):

        # Достаем сырые данные
        titles = response.xpath("//div[@class='sm-category__item ']//h2//a/@title").extract()
        imgs = response.xpath("//div[@class='sm-category__item-photo ']//a//img/@src").extract()
        prices = response.xpath("//div[@class='sm-category__item-actual-price tr']//div[@class='td']//span[@class='rouble']//sm-amount/@params").extract()
        discounts = response.xpath("//div[@class='sm-category__item ']").extract()

        # Дополняем ссылки на картинки
        imgs = [img for img in imgs]

        # Обработка названий
        titles_clean = []
        for title in titles:
            try:
                titles_clean.append(title.split('Велосипед ')[1])
            except IndexError:
                titles_clean.append(title)

        # Обработка цен
        prices_clean = [price.split('value: ')[1] for price in prices]

        # Обработка старых цен
        clean_old_prices = [self.refine(discount, 32) if 
                            'smTileOldpriceBlock smJustify smVMiddle' in discount 
                            else np.nan for discount in discounts]
  
        # Обработка скидок
        clean_discount_prices = [self.refine(discount, 25) if 'smTileOldpriceBlock smJustify smVMiddle' in discount else 0 for discount in discounts]

        for item in zip(titles_clean,prices_clean,clean_old_prices,clean_discount_prices,imgs):
            scraped_info = {
                'title' : item[0],
                'price' : item[1],
                'old_price' : item[2],
                'discount_offer': item[3],
                'image_urls' : [item[4]]}
            yield scraped_info