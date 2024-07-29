# Application class
from dataclasses import dataclass
from .person import Person


@dataclass
class Application:
    applicant: Person
    spo_number: str = None
    submit_method: str = None
    original_certificate: bool = None
