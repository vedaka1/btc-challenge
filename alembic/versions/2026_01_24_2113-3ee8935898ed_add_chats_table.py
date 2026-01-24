"""add_chats_table

Revision ID: 3ee8935898ed
Revises: a3f8e9d4b2c1
Create Date: 2026-01-24 21:13:34.308719

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ee8935898ed'
down_revision: Union[str, Sequence[str], None] = 'a3f8e9d4b2c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'chats',
        sa.Column('oid', sa.Uuid(), nullable=False),
        sa.Column('telegram_chat_id', sa.Integer(), nullable=False),
        sa.Column('chat_type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('oid'),
        sa.UniqueConstraint('telegram_chat_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('chats')
