"""add publishers.from_address (route by sender, not recipient)

Revision ID: 8e3f2a1c9b4d
Revises: 5b9c4f3a8d2e
Create Date: 2026-04-29 04:35:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '8e3f2a1c9b4d'
down_revision = '5b9c4f3a8d2e'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('publishers', sa.Column('from_address', sa.String(320), nullable=True))
    op.create_unique_constraint('publishers_from_address_key', 'publishers', ['from_address'])
    op.alter_column('publishers', 'seed_email_address', nullable=True)
    op.drop_constraint('publishers_seed_email_address_key', 'publishers', type_='unique')

def downgrade():
    op.create_unique_constraint('publishers_seed_email_address_key', 'publishers', ['seed_email_address'])
    op.alter_column('publishers', 'seed_email_address', nullable=False)
    op.drop_constraint('publishers_from_address_key', 'publishers', type_='unique')
    op.drop_column('publishers', 'from_address')
