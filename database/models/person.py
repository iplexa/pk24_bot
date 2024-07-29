# Person class
from dataclasses import dataclass


@dataclass
class Person:
    last_name: str = None
    first_name: str = None
    middle_name: str = None

    @property
    def full_name(self) -> str:
        if self.last_name is None or self.first_name is None or self.middle_name is None:
            return None
        
        return self.last_name + ' ' + self.first_name + (' ' + self.middle_name if self.middle_name != '' else '')
    
    @full_name.setter
    def full_name(self, value) -> None:
        if value is None:
            return None
        
        valid_full_name = self.validate_person_name(full_name=value)

        if valid_full_name is not None:
            self.last_name, self.first_name, self.middle_name = valid_full_name
        else:
            raise ValueError('Full name is not valid')

    @classmethod
    def validate_person_name(cls, full_name: str) -> list[str] | None:
        """
        Возвращает список из фамилии, имени и отчества; в случае отсутствия отчества оно равняется пустой строке
        В случае некорректного ФИО возвращает None
        """

        full_name_splited = full_name.split(' ', 2)

        if len(full_name_splited) < 2:
            return None
        
        if len(full_name_splited) == 2:
            full_name_splited.append('')

        return full_name_splited
