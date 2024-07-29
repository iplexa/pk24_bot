from datetime import datetime
from dataclasses import dataclass


@dataclass
class EmployeesWorktime:
    employee_id: int
    start_time: datetime = None
    end_time: datetime = None
