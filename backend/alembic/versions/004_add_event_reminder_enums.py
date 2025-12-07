"""Add event type and reminder type enums

Revision ID: 004
Revises: 003
Create Date: 2025-12-02

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ENUM types and convert columns."""

    # Create ENUM types
    eventtype_enum = postgresql.ENUM(
        "TASK_CREATED",
        "TASK_UPDATED",
        "TASK_DELETED",
        "ATTACHMENT_ADDED",
        "ATTACHMENT_REMOVED",
        "REMINDER_SENT",
        "LOGIN",
        "PASSWORD_CHANGED",
        name="eventtype",
        create_type=True,
    )
    eventtype_enum.create(op.get_bind(), checkfirst=True)

    remindertype_enum = postgresql.ENUM("DUE_SOON", name="remindertype", create_type=True)
    remindertype_enum.create(op.get_bind(), checkfirst=True)

    # Alter audit_events.event_type column
    op.drop_index("ix_audit_events_event_type", "audit_events")
    op.execute(
        """
        ALTER TABLE audit_events
        ALTER COLUMN event_type TYPE eventtype USING event_type::eventtype
        """
    )
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])

    # Alter reminder_logs.reminder_type column
    op.execute(
        """
        ALTER TABLE reminder_logs
        ALTER COLUMN reminder_type TYPE remindertype USING reminder_type::remindertype
        """
    )


def downgrade() -> None:
    """Revert to VARCHAR columns."""

    # Convert audit_events.event_type back to VARCHAR
    op.drop_index("ix_audit_events_event_type", "audit_events")
    op.execute(
        """
        ALTER TABLE audit_events
        ALTER COLUMN event_type TYPE VARCHAR(100) USING event_type::text
        """
    )
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])

    # Convert reminder_logs.reminder_type back to VARCHAR
    op.execute(
        """
        ALTER TABLE reminder_logs
        ALTER COLUMN reminder_type TYPE VARCHAR(50) USING reminder_type::text
        """
    )

    # Drop ENUM types
    remindertype_enum = postgresql.ENUM(name="remindertype")
    remindertype_enum.drop(op.get_bind(), checkfirst=True)

    eventtype_enum = postgresql.ENUM(name="eventtype")
    eventtype_enum.drop(op.get_bind(), checkfirst=True)
