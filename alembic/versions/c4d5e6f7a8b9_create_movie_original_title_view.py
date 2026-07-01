"""create movie_original_title view

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a7
Create Date: 2026-07-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE VIEW movie_original_title AS
         SELECT movie_id,
            title_name
           FROM ( SELECT row_number() OVER (PARTITION BY movie_title.movie_id ORDER BY movie_title.is_original DESC, movie_title.title_name DESC) AS r,
                    movie_title.movie_id,
                    movie_title.title_name
                   FROM movie_title) temp
          WHERE (r < 2);
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS movie_original_title;")
