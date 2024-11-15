"""init

Revision ID: b9f74c0bc0fe
Revises:
Create Date: 2024-03-22 14:06:47.854099

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b9f74c0bc0fe"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "generation",
        sa.Column(
            "id", sa.Integer(), autoincrement=True, nullable=False, comment="生成ID"
        ),
        sa.Column("status", sa.Boolean(), nullable=True, comment="生成状态"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        comment="生成状态记录表",
    )
    op.create_index(op.f("ix_generation_id"), "generation", ["id"], unique=False)
    op.create_table(
        "instructions",
        sa.Column("id", sa.Integer(), nullable=False, comment="指令ID"),
        sa.Column("name", sa.String(length=128), nullable=False, comment="指令名称"),
        sa.Column(
            "description", sa.String(length=1024), nullable=True, comment="指令描述"
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        comment="提示指令",
    )
    op.create_index(op.f("ix_instructions_id"), "instructions", ["id"], unique=False)
    op.create_table(
        "pattern_preset",
        sa.Column("id", sa.Integer(), nullable=False, comment="纹理ID"),
        sa.Column("name", sa.String(length=128), nullable=False, comment="纹理名称"),
        sa.Column("image", sa.String(length=512), nullable=False, comment="图像链接"),
        sa.Column("prompt", sa.JSON(), nullable=False, comment="纹理提示"),
        sa.Column(
            "instructions", sa.String(length=2048), nullable=True, comment="指令"
        ),
        sa.Column("tags", sa.JSON(), nullable=True, comment="标签"),
        sa.Column("parameters", sa.JSON(), nullable=True, comment="命令参数"),
        sa.Column(
            "description", sa.String(length=1024), nullable=True, comment="风格描述"
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        comment="纹理",
    )
    op.create_index(
        op.f("ix_pattern_preset_id"), "pattern_preset", ["id"], unique=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_pattern_preset_id"), table_name="pattern_preset")
    op.drop_table("pattern_preset")
    op.drop_index(op.f("ix_instructions_id"), table_name="instructions")
    op.drop_table("instructions")
    op.drop_index(op.f("ix_generation_id"), table_name="generation")
    op.drop_table("generation")
    # ### end Alembic commands ###
