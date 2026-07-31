"""Initial schema placeholder — tables added in Phase 1+."""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No tables in Phase 0 — schema begins in Phase 1."""
    pass


def downgrade() -> None:
    """No tables to drop in Phase 0."""
    pass
