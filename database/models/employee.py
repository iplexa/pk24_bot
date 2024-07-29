from dataclasses import dataclass
from .person import Person


@dataclass(kw_only=True)
class Employee(Person):
    id: int
    department: str
    admin: bool
    head: bool
    bitrix_id: int

    @classmethod
    def employee_full_name(self) -> str:
        if self.last_name is None or self.first_name is None:
            return None
        
        return self.first_name + ' ' + self.last_name
    