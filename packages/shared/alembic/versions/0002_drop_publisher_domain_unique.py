"""drop unique on publishers.domain (multi-persona inboxes per publisher)

Revision ID: 5b9c4f3a8d2e
Revises: 2acb3a08baaf
Create Date: 2026-04-29 04:30:00.000000
"""
from alembic import op

revision = '5b9c4f3a8d2e'
down_revision = '2acb3a08baaf'
branch_labels = None
depends_on = None

def upgrade():
    op.drop_constraint('publishers_domain_key', 'publishers', type_='unique')

def downgrade():
    op.create_unique_constraint('publishers_domain_key', 'publishers', ['domain'])
