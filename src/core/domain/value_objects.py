from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Final
import re

@dataclass(frozen=True)
class Money:
    amount: int
    currency: str

    ISO_CURRENCY_REGEX: ClassVar[Final[re.Pattern]] = re.compile(r'^[A-Z]{3}$')
    SUPPORTED: ClassVar[Final[frozenset[str]]] = frozenset({'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'MXN'})

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError(f"Money amount cannot be negative: {self.amount}")
        if not self.ISO_CURRENCY_REGEX.match(self.currency):
            raise ValueError(f"Currency must be ISO 4217 (3 uppercase letters): {self.currency}")
        if self.currency not in self.SUPPORTED:
            raise ValueError(f"Currency {self.currency} not supported. Use: {self.SUPPORTED}")

@dataclass(frozen=True)
class CountryCode:
    code: str

    ALPHA2_REGEX: ClassVar[Final[re.Pattern]] = re.compile(r'^[A-Z]{2}$')

    def __post_init__(self) -> None:
        if not self.ALPHA2_REGEX.match(self.code):
            raise ValueError(f"Country code must be ISO 3166-1 alpha-2: {self.code}")      

class Status(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
