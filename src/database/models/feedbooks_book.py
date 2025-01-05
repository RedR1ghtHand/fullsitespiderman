from sqlalchemy import Column, String, Date
from sqlalchemy.dialects.mysql import TEXT, JSON, INTEGER, BIGINT, FLOAT

from src.database.models import Base
from .mixins import MysqlPrimaryKeyMixin, MysqlTimestampsMixin


class FeedbooksBook(Base, MysqlTimestampsMixin, MysqlPrimaryKeyMixin):
    __tablename__ = 'books'

    external_id = Column('external_id', BIGINT, nullable=True)
    item_url = Column('item_url', String(768), unique=False, nullable=True)
    title = Column('title', String(255), unique=False, nullable=True)
    authors = Column('authors', JSON, nullable=True)
    translators = Column('translators', JSON, nullable=True)
    series_name = Column('series_name', String(255), unique=False, nullable=True)
    series_number = Column('series_number', INTEGER, nullable=True)
    categories = Column('categories', JSON, nullable=True)
    description = Column('description', TEXT, nullable=True)
    publication_date = Column('publication_date', Date, nullable=True)
    publisher = Column('publisher', String(255), unique=False, nullable=True)
    isbn = Column('isbn', String(255), unique=False, nullable=True)
    paper_isbn = Column('paper_isbn', String(255), unique=False, nullable=True)
    language = Column('language', String(255), unique=False, nullable=True)
    page_count = Column('page_count', INTEGER, nullable=True)
    ebook_format = Column('ebook_format', String(255), unique=False, nullable=True)
    ebook_size = Column('ebook_size', String(255), unique=False, nullable=True)
    price = Column('price', FLOAT(10, 2), nullable=True)
    currency = Column('currency', String(3), unique=False, nullable=True)
    image_url = Column('image_url', TEXT, unique=False, nullable=True)
    # image_filename = Column('image_filename', String(255), unique=False, nullable=True)

