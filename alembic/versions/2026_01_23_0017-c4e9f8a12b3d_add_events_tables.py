"""add events tables

Revision ID: c4e9f8a12b3d
Revises: b35e8d2974e7
Create Date: 2026-01-23 00:17:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4e9f8a12b3d'
down_revision: Union[str, Sequence[str], None] = 'b35e8d2974e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create events table
    op.create_table(
        'events',
        sa.Column('oid', sa.Uuid(), nullable=False),
        sa.Column('creator_oid', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('start_at', sa.DateTime(), nullable=False),
        sa.Column('end_at', sa.DateTime(), nullable=False),
        sa.Column('initial_notification_sent', sa.Boolean(), nullable=False),
        sa.Column('reminder_notification_sent', sa.Boolean(), nullable=False),
        sa.Column('start_notification_sent', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['creator_oid'], ['users.oid']),
        sa.PrimaryKeyConstraint('oid')
    )
    
    # Create event_participants table
    op.create_table(
        'event_participants',
        sa.Column('event_oid', sa.Uuid(), nullable=False),
        sa.Column('user_oid', sa.Uuid(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_oid'], ['events.oid']),
        sa.ForeignKeyConstraint(['user_oid'], ['users.oid']),
        sa.PrimaryKeyConstraint('event_oid', 'user_oid')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('event_participants')
    op.drop_table('events')
