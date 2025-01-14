from twisted.enterprise import adbapi
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.sql.expression import ClauseElement
from MySQLdb.cursors import DictCursor

from database.models import FeedbooksBook
from rmq.utils.sql_expressions import compile_expression
import logging


class FeedbooksSQLAlchemyPipeline:
    def __init__(self, db_settings):
        self.db_settings = db_settings

    @classmethod
    def from_crawler(cls, crawler):
        db_settings = {
            'host': crawler.settings.get('DB_HOST'),
            'port': crawler.settings.getint('DB_PORT'),
            'user': crawler.settings.get('DB_USERNAME'),
            'password': crawler.settings.get('DB_PASSWORD'),
            'database': crawler.settings.get('DB_DATABASE')
        }
        return cls(db_settings)

    def open_spider(self, spider):
        self.db_pool = adbapi.ConnectionPool(
            'MySQLdb',
            host=self.db_settings['host'],
            port=self.db_settings['port'],
            user=self.db_settings['user'],
            passwd=self.db_settings['password'],
            db=self.db_settings['database'],
            charset='utf8mb4',
            use_unicode=True,
            cursorclass=DictCursor,
            cp_reconnect=True
        )

    def close_spider(self, spider):
        self.db_pool.close()

    def process_item(self, item, spider):
        self.db_pool.runInteraction(self.process_transaction, item)
        return item

    def process_transaction(self, transaction, item):
        stmt = self.build_store_stmt(item)
        if isinstance(stmt, ClauseElement):
            transaction.execute(*compile_expression(stmt))
        else:
            transaction.execute(stmt)

    def build_store_stmt(self, item):
        stmt = insert(FeedbooksBook).values(
            item_url=item['item_url'],
            title=item['title'],
            authors=item['authors'],
            translators=item['translators'],
            series_name=item['series_name'],
            series_number=item['series_number'],
            categories=item['categories'],
            description=item['description'],
            publication_date=item['publication_date'],
            publisher=item['publisher'],
            isbn=item['isbn'],
            paper_isbn=item['paper_isbn'],
            language=item['lang'],
            page_count=item['page_count'],
            ebook_format=item['ebook_format'],
            ebook_size=item['ebook_size'],
            price=item['price'],
            currency=item['currency'],
            image_url=item['image_urls'][0] if item['image_urls'] else None
        )
        return stmt
