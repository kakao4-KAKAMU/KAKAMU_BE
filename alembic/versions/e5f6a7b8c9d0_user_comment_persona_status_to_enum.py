"""user comment persona status to enum

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-04 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

userstatus = sa.Enum("ACTIVE", "DELETED", name="userstatus")
commentstatus = sa.Enum("ACTIVE", "INACTIVE", name="commentstatus")
personastatus = sa.Enum("ACTIVE", "DELETED", name="personastatus")


def _to_enum(table: str, enum_type: sa.Enum, enum_name: str) -> None:
    enum_type.create(op.get_bind(), checkfirst=True)
    op.execute(f"UPDATE \"{table}\" SET status = 'ACTIVE' WHERE status IS NULL")
    op.execute(f"ALTER TABLE \"{table}\" ALTER COLUMN status DROP DEFAULT")
    op.execute(
        f"ALTER TABLE \"{table}\" ALTER COLUMN status TYPE {enum_name} "
        f"USING status::{enum_name}"
    )
    op.execute(
        f"ALTER TABLE \"{table}\" ALTER COLUMN status SET DEFAULT 'ACTIVE'::{enum_name}"
    )
    op.alter_column(table, "status", existing_type=enum_type, nullable=False)


def _to_varchar(table: str, enum_type: sa.Enum) -> None:
    op.execute(f"ALTER TABLE \"{table}\" ALTER COLUMN status DROP DEFAULT")
    op.execute(
        f"ALTER TABLE \"{table}\" ALTER COLUMN status TYPE VARCHAR(20) "
        f"USING status::text"
    )
    op.execute(f"ALTER TABLE \"{table}\" ALTER COLUMN status SET DEFAULT 'ACTIVE'")
    op.alter_column(
        table,
        "status",
        existing_type=sa.String(length=20),
        nullable=True,
    )
    enum_type.drop(op.get_bind(), checkfirst=True)


def upgrade() -> None:
    _to_enum("user", userstatus, "userstatus")
    _to_enum("comment", commentstatus, "commentstatus")
    _to_enum("persona", personastatus, "personastatus")


def downgrade() -> None:
    _to_varchar("persona", personastatus)
    _to_varchar("comment", commentstatus)
    _to_varchar("user", userstatus)
