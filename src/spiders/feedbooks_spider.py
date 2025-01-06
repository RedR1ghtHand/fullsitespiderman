import scrapy
from datetime import datetime, timedelta
import re
import json
from items import FeedbooksItem
import time

class FeedbooksSpider(scrapy.Spider):
    name = 'fbs'
    allowed_domains = ["feedbooks.com"]

    def start_requests(self):
        # Define date range
        start_date = datetime(2000, 1, 10)
        while start_date < datetime(2025, 1, 1):
            end_date = start_date + timedelta(days=30)  # +1 month range
            url = (f"https://market.feedbooks.com/search?languages=all"
                   f"&publication_date_end={end_date.strftime('%Y-%m-%d')}"
                   f"&publication_date_start={start_date.strftime('%Y-%m-%d')}")
            yield scrapy.Request(url, callback=self.parse_page, meta={'start_date': start_date, 'end_date': end_date, 'page': 1, 'retry_count': 0})
            start_date = end_date + timedelta(days=30)  # Move to next range

    def parse_page(self, response):
        # Check for rate limit (429)
        if response.status == 429:
            retry_count = response.meta['retry_count'] + 1
            if retry_count <= 5:
                wait_time = 2 ** retry_count  # Exponential backoff
                self.logger.warning(f"429 Rate Limit. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                yield scrapy.Request(response.url, callback=self.parse_page, meta={**response.meta, 'retry_count': retry_count}, dont_filter=True)
            else:
                self.logger.error(f"Max retries reached for {response.url}")
            return

        # Extract book links
        book_links = response.css('a.b-details__title::attr(href)').getall()
        if not book_links:
            self.logger.warning(f"No book links found for {response.meta['start_date']} - {response.meta['end_date']}, page {response.meta['page']}.")
        else:
            self.logger.info(f"Found {len(book_links)} books for {response.meta['start_date']} - {response.meta['end_date']}, page {response.meta['page']}.")

        # Process each book link
        for link in book_links:
            absolute_url = response.urljoin(link)
            self.logger.debug(f"Book link: {absolute_url}")
            yield response.follow(absolute_url, callback=self.parse_item)

        # Handle pagination
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_page, meta=response.meta)

    def parse_item(self, response):
        # Extract book details
        title = response.css('h1.item__title::text').get(default='').strip()
        external_id = response.url.split('/')[-1]
        description = response.xpath('//div[@class="item__description tabbed"]/text()').get(default='').strip()
        categories = response.css('div.item__chips a::text').getall()
        series_name = response.xpath('//div[@class="item__subtitle"]/a/text()').get(default='').strip()
        series_number = response.xpath('//div[@class="item__subtitle"]/span[contains(text(), "#")]/text()').re_first(r'#(\d+)')
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
        iso_date = datetime.strptime(publication_date.strip(), '%B %d, %Y').date().isoformat() if publication_date else None
        lang = response.xpath('//div[text()="Language"]/following-sibling::div/text()').get()
        protection = None
        epub_isbn = response.xpath('//div[text()="EPUB ISBN"]/following-sibling::div/text()').get()
        paper_isbn = response.xpath('//div[text()="Paper ISBN"]/following-sibling::div/text()').get()
        image_url = response.css('div.item__cover img::attr(src)').get()

        # Populate item
        item = FeedbooksItem(
            title=title,
            item_url=response.url,
            description=description.replace("'", "''"),
            categories=json.dumps(categories),
            series_name=series_name,
            series_number=int(series_number) if series_number else 0,
            authors=json.dumps(authors),
            translators=json.dumps(translators),
            price=price,
            currency=currency,
            ebook_format=ebook_format,
            page_count=int(page_count),
            publisher=publisher.replace("'", "''"),
            publication_date=iso_date,
            lang=lang,
            protection_method=protection,
            isbn=epub_isbn,
            paper_isbn=paper_isbn,
            image_urls=[image_url],
            ebook_size=ebook_size,
            external_id=external_id
        )

        yield item
