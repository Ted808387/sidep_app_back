"""Add avatar_url and notification settings to User model, add BlacklistedToken model

Revision ID: 48fe15c40274
Revises: 
Create Date: 2025-07-21 18:11:58.009375

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48fe15c40274'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('email_notifications_enabled', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('sms_notifications_enabled', sa.Boolean(), nullable=True))
    op.alter_column('users', 'avatar_url',
               existing_type=sa.TEXT(),
               type_=sa.String(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'avatar_url',
               existing_type=sa.String(),
               type_=sa.TEXT(),
               existing_nullable=True)
    op.drop_column('users', 'sms_notifications_enabled')
    op.drop_column('users', 'email_notifications_enabled')
    # ### end Alembic commands ###
