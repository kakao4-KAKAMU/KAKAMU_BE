"""update movie evaluation schema

Revision ID: a1b2c3d4e5f6
Revises: 56c09e54d49b
Create Date: 2026-06-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "56c09e54d49b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("movie_evaluation", sa.Column("user_id", sa.UUID(), nullable=True))

    op.execute(
        """
        UPDATE movie_evaluation me
        SET user_id = p.user_id
        FROM persona p
        WHERE me.persona_id = p.id
        """
    )
    op.execute("DELETE FROM movie_evaluation WHERE user_id IS NULL")

    op.alter_column("movie_evaluation", "user_id", nullable=False)
    op.create_foreign_key(
        "fk_movie_evaluation_user_id",
        "movie_evaluation",
        "user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.alter_column("movie_evaluation", "persona_id", nullable=True)

    op.execute(
        """
        DELETE FROM movie_evaluation
        WHERE movie_id !~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
        """
    )

    op.alter_column(
        "movie_evaluation",
        "movie_id",
        existing_type=sa.String(length=50),
        type_=postgresql.UUID(as_uuid=True),
        postgresql_using="movie_id::uuid",
        existing_nullable=False,
    )
    op.create_foreign_key(
        "fk_movie_evaluation_movie_id",
        "movie_evaluation",
        "movie",
        ["movie_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("uq_movie_evaluation_persona_movie", "movie_evaluation", type_="unique")

    op.create_index(
        "uq_movie_evaluation_persona_movie",
        "movie_evaluation",
        ["persona_id", "movie_id"],
        unique=True,
        postgresql_where=sa.text("persona_id IS NOT NULL"),
    )
    op.create_index(
        "uq_movie_evaluation_user_movie",
        "movie_evaluation",
        ["user_id", "movie_id"],
        unique=True,
        postgresql_where=sa.text("persona_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_movie_evaluation_user_movie", table_name="movie_evaluation")
    op.drop_index("uq_movie_evaluation_persona_movie", table_name="movie_evaluation")

    op.drop_constraint("fk_movie_evaluation_movie_id", "movie_evaluation", type_="foreignkey")
    op.alter_column(
        "movie_evaluation",
        "movie_id",
        existing_type=postgresql.UUID(as_uuid=True),
        type_=sa.String(length=50),
        postgresql_using="movie_id::text",
        existing_nullable=False,
    )

    op.drop_constraint("fk_movie_evaluation_user_id", "movie_evaluation", type_="foreignkey")
    op.drop_column("movie_evaluation", "user_id")

    op.alter_column("movie_evaluation", "persona_id", nullable=False)

    op.create_unique_constraint(
        "uq_movie_evaluation_persona_movie",
        "movie_evaluation",
        ["persona_id", "movie_id"],
    )
