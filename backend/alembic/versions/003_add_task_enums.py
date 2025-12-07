"""Add task status and priority enums

Revision ID: 003
Revises: 002
Create Date: 2025-12-02

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ENUM types and convert columns."""

    # Create ENUM types
    taskstatus_enum = postgresql.ENUM(
        "TODO", "IN_PROGRESS", "DONE", "BLOCKED", name="taskstatus", create_type=True
    )
    taskstatus_enum.create(op.get_bind(), checkfirst=True)

    taskpriority_enum = postgresql.ENUM(
        "LOW", "MEDIUM", "HIGH", "CRITICAL", name="taskpriority", create_type=True
    )
    taskpriority_enum.create(op.get_bind(), checkfirst=True)

    # Alter columns to use ENUM types
    # Drop indexes first
    op.drop_index("ix_tasks_status", "tasks")
    op.drop_index("ix_tasks_priority", "tasks")

    # Alter columns
    op.execute(
        """
        ALTER TABLE tasks
        ALTER COLUMN status TYPE taskstatus USING status::taskstatus
        """
    )
    op.execute(
        """
        ALTER TABLE tasks
        ALTER COLUMN priority TYPE taskpriority USING priority::taskpriority
        """
    )

    # Recreate indexes
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_priority", "tasks", ["priority"])


def downgrade() -> None:
    """Revert to VARCHAR columns."""

    # Drop indexes
    op.drop_index("ix_tasks_priority", "tasks")
    op.drop_index("ix_tasks_status", "tasks")

    # Convert columns back to VARCHAR
    op.execute(
        """
        ALTER TABLE tasks
        ALTER COLUMN status TYPE VARCHAR(50) USING status::text
        """
    )
    op.execute(
        """
        ALTER TABLE tasks
        ALTER COLUMN priority TYPE VARCHAR(50) USING priority::text
        """
    )

    # Recreate indexes
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_priority", "tasks", ["priority"])

    # Drop ENUM types
    taskpriority_enum = postgresql.ENUM(name="taskpriority")
    taskpriority_enum.drop(op.get_bind(), checkfirst=True)

    taskstatus_enum = postgresql.ENUM(name="taskstatus")
    taskstatus_enum.drop(op.get_bind(), checkfirst=True)
