from alembic import op


revision = "20260427_0002"
down_revision = "20260426_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS ix_virtual_machines_current_user_id ON virtual_machines (current_user_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_virtual_machines_current_user_id")
