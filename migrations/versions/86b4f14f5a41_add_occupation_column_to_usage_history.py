"""Add occupation column to usage_history

Revision ID: 86b4f14f5a41
Revises: 
Create Date: 2024-12-27 21:24:28.947740

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86b4f14f5a41'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('usage_history', schema=None) as batch_op:
        batch_op.add_column(sa.Column('occupation', sa.String(length=50), nullable=False, server_default='不明'))
        batch_op.add_column(sa.Column('health_focus', sa.String(length=200), nullable=False, server_default='不明'))
        batch_op.add_column(sa.Column('values', sa.String(length=200), nullable=False, server_default='不明'))

    # ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('usage_history', schema=None) as batch_op:
        batch_op.drop_column('occupation')
        batch_op.drop_column('health_focus')
        batch_op.drop_column('values')

    # ### end Alembic commands ###
