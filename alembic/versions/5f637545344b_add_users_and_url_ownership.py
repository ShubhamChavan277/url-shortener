"""Add users and URL ownership

Revision ID: 5f637545344b
Revises: 8da5a6f879d4
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5f637545344b"
down_revision: Union[str, Sequence[str], None] = "8da5a6f879d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_users_email"),
        "users",
        ["email"],
        unique=True,
    )

    op.add_column(
        "urls",
        sa.Column("user_id", sa.Integer(), nullable=False),
    )
    op.add_column(
        "urls",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_urls_user_id"),
        "urls",
        ["user_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_urls_user_id_users",
        "urls",
        "users",
        ["user_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_urls_user_id_users",
        "urls",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_urls_user_id"), table_name="urls")
    op.drop_column("urls", "expires_at")
    op.drop_column("urls", "user_id")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
