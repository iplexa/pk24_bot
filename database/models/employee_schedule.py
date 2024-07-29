from dataclasses import dataclass
from datetime import datetime


@dataclass
class EmployeeSchedule:
    employee_id: int
    start_datetime: datetime
    end_datetime: datetime

