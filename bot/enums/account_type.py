from enum import Enum
from typing import Sequence, List, Self

from app.database.models import Role


class AccountType(Enum):
    ADMINISTRATOR = "administrator"
    MANAGER = "manager"
    SUPERVISOR = "supervisor"
    PARENT = "parent"

    @classmethod
    def get_main_role(
            cls,
            roles: Sequence[Role]
    ) -> Self | None:
        parsed_roles: List[AccountType] = cls.from_sequence(roles)

        for account_type in cls:
            if account_type in parsed_roles:
                return account_type

    @staticmethod
    def from_sequence(role_sequence: Sequence[Role]) -> List['AccountType']:
        return list(
            map(
                lambda role: AccountType(role.account_type.value),
                role_sequence
            )
        )
