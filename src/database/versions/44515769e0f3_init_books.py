"""init_books

Revision ID: 44515769e0f3
Revises: 
Create Date: 2025-01-04 13:31:51.195089

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '44515769e0f3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'books',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),

        sa.Column('external_id', sa.BigInteger(), nullable=True),
        sa.Column('item_url', sa.String(768), nullable=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('authors', sa.JSON, nullable=True),
        sa.Column('translators', sa.JSON, nullable=True),
        sa.Column('series_name', sa.String(255), nullable=True),
        sa.Column('series_number', sa.Integer(), nullable=True),
        sa.Column('categories', sa.JSON, nullable=True),
        sa.Column('description', sa.TEXT, nullable=True),
        sa.Column('publication_date', sa.Date, nullable=True),
        sa.Column('publisher', sa.String(255), nullable=True),
        sa.Column('isbn', sa.String(255), nullable=True),
        sa.Column('paper_isbn', sa.String(255), nullable=True),
        sa.Column('language', sa.String(255), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('ebook_format', sa.String(255), nullable=True),
        sa.Column('ebook_size', sa.String(255), nullable=True),
        sa.Column('protection_method', sa.String(255), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(3), nullable=True),
        sa.Column('image_url', sa.TEXT, nullable=True),
    )


def downgrade():
    op.drop_table('books')
