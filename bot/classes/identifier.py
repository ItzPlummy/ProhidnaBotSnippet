from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.bot.enums.account_type import AccountType
from app.database.models import Account, Settings


class Identifier:
    def __init__(self):
        pass

    @staticmethod
    async def identify(
            account_id: UUID | str,
            telegram_id: int,
            db: AsyncSession
    ) -> AccountType | None:
        account: Account = await db.scalar(
            select(Account).
            filter_by(id=account_id).
            options(
                joinedload(Account.roles),
                joinedload(Account.settings)
            )
        )

        if account is None:
            return

        await db.execute(
            update(Account).
            filter_by(id=account_id).
            values(telegram_id=telegram_id)
        )

        if account.settings is None:
            db.add(Settings(account_id=account_id))

        await db.commit()

        return AccountType.get_main_role(account.roles)

    @staticmethod
    async def unidentify(
            telegram_id: int,
            db: AsyncSession
    ) -> None:
        await db.execute(
            update(Account).
            filter_by(telegram_id=telegram_id).
            values(telegram_id=None)
        )

        await db.commit()
