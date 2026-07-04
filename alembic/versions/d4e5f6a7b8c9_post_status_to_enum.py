"""post status to enum

Revision ID: d4e5f6a7b8c9
Revises: b2c3d4e5f6a7
Create Date: 2026-07-04 16:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

poststatus = sa.Enum("ACTIVE", "INACTIVE", name="poststatus")


def upgrade() -> None:
    poststatus.create(op.get_bind(), checkfirst=True)
    op.execute("UPDATE post SET status = 'ACTIVE' WHERE status IS NULL")
    op.execute("ALTER TABLE post ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "ALTER TABLE post ALTER COLUMN status TYPE poststatus "
        "USING status::poststatus"
    )
    op.execute("ALTER TABLE post ALTER COLUMN status SET DEFAULT 'ACTIVE'::poststatus")
    op.alter_column("post", "status", existing_type=poststatus, nullable=False)


def downgrade() -> None:
    op.execute("ALTER TABLE post ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "ALTER TABLE post ALTER COLUMN status TYPE VARCHAR(20) "
        "USING status::text"
    )
    op.execute("ALTER TABLE post ALTER COLUMN status SET DEFAULT 'ACTIVE'")
    op.alter_column(
        "post",
        "status",
        existing_type=sa.String(length=20),
        nullable=True,
    )
    poststatus.drop(op.get_bind(), checkfirst=True)
