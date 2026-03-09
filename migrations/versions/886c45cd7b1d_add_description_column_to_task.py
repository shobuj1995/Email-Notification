"""add description column to task

Revision ID: 886c45cd7b1d
Revises: 6d693db56223
Create Date: 2026-03-09 11:14:00.689922
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '886c45cd7b1d'
down_revision = '6d693db56223'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.drop_column('description')