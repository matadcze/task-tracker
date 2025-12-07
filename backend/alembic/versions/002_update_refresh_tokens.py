"""Update refresh_tokens table schema

Revision ID: 002
Revises: 001
Create Date: 2025-12-02

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update refresh_tokens table to use token_hash and revoked."""

    # Drop old indexes
    op.drop_index("ix_refresh_tokens_token", "refresh_tokens")

    # Rename token column to token_hash and change length
    op.alter_column(
        "refresh_tokens",
        "token",
        new_column_name="token_hash",
        type_=sa.String(length=255),
    )

    # Replace revoked_at with revoked boolean
    op.drop_column("refresh_tokens", "revoked_at")
    op.add_column(
        "refresh_tokens",
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
    )

    # Drop created_at column (not used in model)
    op.drop_column("refresh_tokens", "created_at")

    # Create new indexes
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])
    op.create_index("ix_refresh_tokens_revoked", "refresh_tokens", ["revoked"])


def downgrade() -> None:
    """Revert refresh_tokens table changes."""

    # Drop new indexes
    op.drop_index("ix_refresh_tokens_revoked", "refresh_tokens")
    op.drop_index("ix_refresh_tokens_expires_at", "refresh_tokens")
    op.drop_index("ix_refresh_tokens_token_hash", "refresh_tokens")

    # Add back created_at
    op.add_column(
        "refresh_tokens",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Revert revoked to revoked_at
    op.drop_column("refresh_tokens", "revoked")
    op.add_column(
        "refresh_tokens",
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
    )

    # Rename token_hash back to token
    op.alter_column(
        "refresh_tokens",
        "token_hash",
        new_column_name="token",
        type_=sa.String(length=500),
    )

    # Create old index
    op.create_index("ix_refresh_tokens_token", "refresh_tokens", ["token"])
