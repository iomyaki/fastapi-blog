"""migration2

Revision ID: 4ef4bd2e37db
Revises: a8377078244c
Create Date: 2025-01-19 15:00:35.085717

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4ef4bd2e37db"
down_revision: Union[str, None] = "a8377078244c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("users", sa.Column("password", sa.String(length=20), nullable=False))
    op.drop_column("users", "name")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "users",
        sa.Column("name", sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    )
    op.drop_column("users", "password")
    # ### end Alembic commands ###
