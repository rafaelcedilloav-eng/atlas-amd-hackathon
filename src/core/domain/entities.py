from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from src.core.domain.value_objects import Money, CountryCode, Status

@dataclass
class Transaction:
    id: UUID = field(default_factory=uuid4)
    amount: Money
    country: CountryCode
    status: Status
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transaction):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
