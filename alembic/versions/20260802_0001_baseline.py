"""baseline: точка отсчёта для схемы, созданной через create_all()

Ревизия намеренно пустая. Она нужна только для того, чтобы Alembic
знал, от какого состояния считать изменения.

Сами таблицы по-прежнему создаёт init_db() через Base.metadata.create_all().
Новые таблицы он тоже создаст сам. А вот всё остальное — новые колонки,
переименования, индексы, засыпка данных — с этого момента только через
миграции.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-08-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
