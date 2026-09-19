"""Initial OrderFlow schema."""
from alembic import op
import sqlalchemy as sa

revision = "20260916_0001"
down_revision = None
branch_labels = None
depends_on = None

user_role = sa.Enum("admin", "staff", name="user_role")
order_status = sa.Enum("pending", "paid", "shipped", "delivered", "cancelled", name="order_status")


def timestamps():
    return [sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)]


def upgrade():
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(320), nullable=False), sa.Column("full_name", sa.String(120), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("role", user_role, nullable=False), sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False), *timestamps(), sa.UniqueConstraint("email", name="uq_users_email"))
    op.create_index("ix_users_email", "users", ["email"]); op.create_index("ix_users_role", "users", ["role"]); op.create_index("ix_users_is_active", "users", ["is_active"])
    op.create_table("customers", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("email", sa.String(320), nullable=False), sa.Column("phone", sa.String(40), nullable=False), sa.Column("address", sa.Text(), nullable=False), *timestamps(), sa.UniqueConstraint("email", name="uq_customers_email"))
    op.create_index("ix_customers_name", "customers", ["name"]); op.create_index("ix_customers_email", "customers", ["email"])
    op.create_table("products", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("sku", sa.String(64), nullable=False), sa.Column("name", sa.String(160), nullable=False), sa.Column("description", sa.Text(), server_default="", nullable=False), sa.Column("price", sa.Numeric(12, 2), nullable=False), sa.Column("stock_quantity", sa.Integer(), nullable=False), sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False), *timestamps(), sa.CheckConstraint("price >= 0", name="ck_products_price_nonnegative"), sa.CheckConstraint("stock_quantity >= 0", name="ck_products_stock_nonnegative"), sa.UniqueConstraint("sku", name="uq_products_sku"))
    op.create_index("ix_products_sku", "products", ["sku"]); op.create_index("ix_products_name", "products", ["name"]); op.create_index("ix_products_is_active", "products", ["is_active"])
    op.create_table("orders", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("order_number", sa.String(32), nullable=False), sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False), sa.Column("status", order_status, nullable=False), sa.Column("total_amount", sa.Numeric(12, 2), nullable=False), sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), *timestamps(), sa.UniqueConstraint("order_number", name="uq_orders_order_number"))
    for column in ("order_number", "customer_id", "status", "created_by"): op.create_index(f"ix_orders_{column}", "orders", [column])
    op.create_table("order_items", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False), sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False), sa.Column("quantity", sa.Integer(), nullable=False), sa.Column("unit_price", sa.Numeric(12, 2), nullable=False), sa.Column("line_total", sa.Numeric(12, 2), nullable=False), sa.CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"), sa.CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_nonnegative"), sa.CheckConstraint("line_total >= 0", name="ck_order_items_line_total_nonnegative"), sa.UniqueConstraint("order_id", "product_id", name="uq_order_items_order_product"))
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"]); op.create_index("ix_order_items_product_id", "order_items", ["product_id"])


def downgrade():
    op.drop_table("order_items"); op.drop_table("orders"); op.drop_table("products"); op.drop_table("customers"); op.drop_table("users")
