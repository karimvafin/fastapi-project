"""add_grades_to_users_and_tasks

Revision ID: 87e4be17ac91
Revises: e24571d4d879
Create Date: 2025-05-04 22:56:14.494260

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '87e4be17ac91'
down_revision: Union[str, None] = 'e24571d4d879'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('task', sa.Column('grade', sa.Integer(), nullable=True))
    op.add_column('user', sa.Column('grade', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'grade')
    op.drop_column('task', 'grade')
    # ### end Alembic commands ###