import scrapy

import re
import json
from datetime import datetime, timedelta

from items import FeedbooksItem


class FeedbooksSpider(scrapy.Spider):
    """
    Problem: The website returns the same results after page 200, regardless of the query.
    As a result, it is impossible to fetch all 1M+ books without splitting results into chunks.

    Solution: Advanced Search filter by Publication Date
        1. generate_date_ranges() - Generates all possible "chunks" of book publication dates,
           starting from the first available book on the site to today.
        2. start_requests() - Initializes the spider by iterating through the generated date ranges
           and sending requests for each range to ensure every chunk of data is processed.
        3. parse_page() - Extracts links to books and handles pagination.
        4. parse_item() - Extracts book details from individual book pages.
    """
    name = 'fbs'
    allowed_domains = ['market.feedbooks.com']
    base_url = "https://market.feedbooks.com/search?languages=all"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_date = datetime(1950, 1, 1)
        self.end_date = datetime.today()
        self.delta = timedelta(days=30)
        self.date_ranges = self.generate_date_ranges()
        self.logger.info(f"Generated {len(self.date_ranges)} date ranges.")

    def generate_date_ranges(self):
        ranges = []
        current_start = self.start_date
        while current_start < self.end_date:
            current_end = min(current_start + self.delta, self.end_date)
            ranges.append((current_start, current_end))
            current_start = current_end
        return ranges

    def build_url(self, start_date, end_date):
        return (f"{self.base_url}&publication_date_start={start_date.strftime('%Y-%m-%d')}"
                f"&publication_date_end={end_date.strftime('%Y-%m-%d')}")

    def start_requests(self):
        for start_date, end_date in self.date_ranges:
            url = self.build_url(start_date, end_date)
            self.logger.info(f"Starting request for range: {start_date} - {end_date}")
            yield scrapy.Request(url, callback=self.parse_page)

    def parse_page(self, response):
        # Extract book links
        book_links = response.css('a.b-details__title::attr(href)').getall()
        if book_links:
            self.logger.info(f"Found {len(book_links)} books on page: {response.url}")
            for link in book_links:
                yield response.follow(link, callback=self.parse_item)
        else:
            self.logger.info(f"No books found on page: {response.url}")

        # Follow pagination
        next_page = response.css(
            'a.button.pagination__navigator[data-post-hog="catalog-changepage-next"]::attr(href)'
        ).get()
        self.logger.info(f"nextpage: {next_page}")
        if next_page:
            self.logger.info(f"Navigating to next page: {next_page}")
            yield response.follow(next_page, callback=self.parse_page)

    def parse_item(self, response):
        # Extract book details
        title = response.css('h1.item__title::text').get().strip()
        description = response.xpath('//*[@id="item-description"]/p/text()').getall()
        categories = response.css('div.item__chips a::text').getall()
        series_name = response.xpath('//div[@class="item__subtitle"]/a/text()').get(default='').strip()
        series_number = response.xpath('//div[@class="item__subtitle"]/span[contains(text(), "#")]/text()').re_first(
            r'#(\d+)')
        authors = response.css('a[data-post-hog="productpage-publication-author"]::text').getall()
        translators = response.css('a[data-post-hog="productpage-publication-contributor"]::text').getall()

        # Price and currency
        price_info = response.xpath('//a[contains(@class, "item__buy")]/text()').get()
        match = re.search(r'(\D*)(\d+(\.\d+)?)', price_info) if price_info else None
        currency = match.group(1).strip() if match else '€'
        price = float(match.group(2)) if match else 0

        # Additional metadata
        ebook_format = response.xpath('//div[text()="Format"]/following-sibling::div/text()').get()
        ebook_size = response.xpath('//div[contains(text(), "File size")]/following-sibling::div/text()').get()
        page_count = response.xpath('//div[text()="Page count"]/following-sibling::div/text()').get(default='0')
        publisher = response.xpath('//div[text()="Publisher"]/following-sibling::div/a/text()').get(default='').strip()
        publication_date = response.xpath('//div[text()="Publication date"]/following-sibling::div/text()').get()
        iso_date = datetime.strptime(publication_date.strip(),
                                     '%B %d, %Y').date().isoformat() if publication_date else None
        lang = response.xpath('//div[text()="Language"]/following-sibling::div/text()').get()
        epub_isbn = response.xpath('//div[text()="EPUB ISBN"]/following-sibling::div/text()').get()
        paper_isbn = response.xpath('//div[text()="Paper ISBN"]/following-sibling::div/text()').get()
        image_url = response.css('div.item__cover img::attr(src)').get()

        # Populate item
        item = FeedbooksItem(
            title=title,
            item_url=response.url,
            description=json.dumps(description),
            categories=json.dumps(categories),
            series_name=series_name,
            series_number=int(series_number) if series_number else 0,
            authors=json.dumps(authors),
            translators=json.dumps(translators),
            price=price,
            currency=currency,
            ebook_format=ebook_format,
            page_count=int(page_count),
            publisher=publisher,
            publication_date=iso_date,
            lang=lang,
            isbn=epub_isbn,
            paper_isbn=paper_isbn,
            image_urls=[image_url],
            ebook_size=ebook_size,
        )

        yield item
