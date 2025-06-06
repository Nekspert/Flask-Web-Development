"""Added body_html field to Post model

Revision ID: 58e7c0043395
Revises: 9dcc17db78ba
Create Date: 2025-05-29 14:27:16.187593

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '58e7c0043395'
down_revision = '9dcc17db78ba'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('posts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('body_html', sa.Text(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('posts', schema=None) as batch_op:
        batch_op.drop_column('body_html')

    # ### end Alembic commands ###
