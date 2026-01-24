"""remove end_at and initial_notification_sent

Revision ID: a3f8e9d4b2c1
Revises: ed2d0c957372
Create Date: 2026-01-24 20:37:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f8e9d4b2c1'
down_revision: Union[str, Sequence[str], None] = 'ed2d0c957372'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop columns that are no longer needed
    op.drop_column('events', 'end_at')
    op.drop_column('events', 'initial_notification_sent')
    
    # Add new completed_at column
    op.add_column('events', sa.Column('completed_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Restore removed columns
    op.add_column('events', sa.Column('end_at', sa.DateTime(), nullable=False))
    op.add_column('events', sa.Column('initial_notification_sent', sa.Boolean(), nullable=False))
    
    # Drop completed_at column
    op.drop_column('events', 'completed_at')
