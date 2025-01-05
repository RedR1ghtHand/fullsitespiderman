import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from src.items import FeedbooksItem
import json


class FeedbooksSpider(CrawlSpider):
    name = 'fbooks_spider'
    allowed_domains = ["feedbooks.com"]

    rules = (
        Rule(LinkExtractor(allow="item/",
                           deny=("buy", "login", 'preview', 'locale', 'content')),
             callback='parse_item'),
        Rule(LinkExtractor(allow=r"/search\?advanced_search=true&lang=all&page=\d+&publication_date_end=\d{4}-\d{2}-\d{2}&publication_date_start=\d{4}-\d{2}-\d{2}"),
             follow=True),
    )

    def start_requests(self):
        start_date = "1950-01-01"
        end_date = "2025-01-01"
        date_format = "%Y-%m-%d"
        current_date = start_date

        while current_date < end_date:
            url = f"https://www.feedbooks.com/search?advanced_search=true&lang=all&page=1&publication_date_end={current_date}&publication_date_start={current_date}"
            yield scrapy.Request(url)
            current_date = (datetime.strptime(current_date, date_format) + relativedelta(months=1)).strftime(
                date_format)

    def parse_item(self, response):
        total_pages = response.xpath('//*[@id="content"]/section[3]/div[4]/div[1]/div/a[5]/text()').get()
        if total_pages:
            for page_num in range(2, int(total_pages)+1):
                page_ulr = "https://www.feedbooks.com/recent?lang=all&page={}"
                yield scrapy.Request(page_ulr.format(page_num))

        title = response.css('h1.item__title::text').get().strip()
        external_id = response.url.split('/')[-1]
        item_description = (response.xpath('//div[@class="item__description tabbed"]')
                            .xpath('normalize-space(string())').get())
        item_description_normalized = item_description.replace("'", "''")

        categories = [category.replace("'", "''") for category in response.xpath(
            '//div[@class="item__chips"]//a//text()').getall()
        ]
        series_name = response.xpath('//div[@class="item__subtitle"]'
                                     '//*[contains(text(), "#")]/preceding-sibling::a//text()').get(),
        series_number = response.xpath('//div[@class="item__subtitle"]/a[@class="link"]'
                                       '/following-sibling::span[contains(text(), "#")]//text()').get()
        if series_number:
            series_number = series_number.replace('#', '').replace(' ', '')
        else:
            series_number = 0

        authors = [
            author.replace("'", "''") for author in response.xpath(
                '//div[@class="item__subtitle"]/a[@data-post-hog="productpage-publication-author"]/text()').getall()
        ]

        translators = [
            translator.replace("'", "''") for translator in
            response.xpath('//div[@class="item__subtitle"]'
                           '/a[@data-post-hog="productpage-publication-contributor"]/text()').getall()
        ]

        price_info = response.xpath('//a[contains(@class, "item__buy")]/text()').get()
        match = re.search(r'(\D*)(\d+(\.\d+)?)', price_info.split()[-1]) if price_info else None
        currency = match.group(1).strip() if match else '€'
        price = match.group(2) if match else 0

        ebook_format = response.xpath(
            '//div[@class="item-details__key"][text()="Format"]'
            '/following-sibling::div[@class="item-details__value"]/text()').get()
        ebook_size = response.xpath(
            '//div[@class="item-details__key"][contains(text(), "File size")]'
            '/following-sibling::div/text()').get(),
        page_count = response.xpath(
            '//div[@class="item-details__key"][text()="Page count"]'
            '/following-sibling::div[@class="item-details__value"]/text()').get()
        if not page_count:
            page_count = 0

        publisher = response.xpath('//div[@class="item-details__key"][text()="Publisher"]'
                                   '/following-sibling::div[@class="item-details__value"]/a/text()').get()
        publication_date = response.xpath('//div[@class="item-details__key"][text()="Publication date"]'
                                          '/following-sibling::div[@class="item-details__value"]/text()').get()
        iso_date = datetime.strptime(publication_date.strip(),
                                     '%B %d, %Y').date().isoformat() if publication_date else None

        lang = response.xpath('//div[@class="item-details__key"][text()="Language"]'
                              '/following-sibling::div[@class="item-details__value"]/text()').get()
        protection = response.xpath('//div[@class="item-details__key"][text()="Protection"]'
                                    '/following-sibling::div[@class="item-details__value"]/text()').get().strip()
        epub_isbn = response.xpath('//div[@class="item-details__key"][text()="EPUB ISBN"]'
                                   '/following-sibling::div[@class="item-details__value"]/text()').get()
        paper_isbn = response.xpath('//div[@class="item-details__key"][text()="Paper ISBN"]'
                                    '/following-sibling::div[@class="item-details__value"]/text()').get()

        image_url = response.xpath('//div[@class="item__cover"]//@src').get()

        item = FeedbooksItem(
            title=title,
            item_url=response.url,
            description=item_description_normalized,
            categories=json.dumps(categories),
            series_name=series_name[0],
            series_number=series_number,
            authors=json.dumps(authors),
            translators=json.dumps(translators),
            price=price,
            currency=currency,
            ebook_format=ebook_format,
            page_count=page_count,
            publisher=publisher,
            publication_date=iso_date,
            lang=lang,
            protection_method=protection,
            isbn=epub_isbn,
            paper_isbn=paper_isbn,
            image_urls=[image_url],
            ebook_size=ebook_size[0],
            external_id=external_id
        )

        yield item



