# Database class
import asyncio
from typing import Coroutine
from datetime import datetime, date, timedelta

import inspect
import psycopg

from .models import Employee, EmployeesWorktime, EmployeeSchedule



class Database:
    def __init__(self, on_error_callback: callable) -> None:
        self._db = None
        self.on_error_callback = on_error_callback
    
    async def login(self):
        self._db = await psycopg.AsyncConnection.connect(
            dbname="pk24_test",
            user="serviceskmpo",
            password="Kameta2013!",
            host="77.232.135.162",
            port="5432",
            row_factory=psycopg.rows.dict_row
        )

    async def _make_base_query(self, sql: str, data: dict = {},
                               fetch_all: bool = False, commit_needed: bool = False,
                               on_error_callback: Coroutine = None):
        cursor = self._db.cursor()

        try:
            await cursor.execute(sql, data)

            if commit_needed:
                await self._db.commit()
                return True
            else:    
                if fetch_all:
                    return await cursor.fetchall()
                else:
                    return await cursor.fetchone()
        except psycopg.Error as error:
            await self._db.rollback()
            caller_function_name = inspect.stack()[1][0].f_code.co_name

            if on_error_callback is None:
                self.on_error_callback(error, sql, data, caller_function_name)
            else:
                await on_error_callback(error, sql, data, caller_function_name)

            return False
        finally:
            await cursor.close()
    
    async def get_employee(self, all: bool = False, **employee_fields) -> Employee | list[Employee]:
        employees = []

        sql = 'select * from employees'
        data = {}

        if employee_fields:
            sql += ' where'

            for field_name, field_value in employee_fields.items():
                sql += f' {field_name} = %({field_name})s '
                data[field_name] = field_value
        
        raw_employees = await self._make_base_query(sql=sql, data=data, fetch_all=True if all else False)

        if raw_employees is not None:
            if isinstance(raw_employees, dict):
                raw_employees = [raw_employees]

            for raw_employee in raw_employees:
                employees.append(Employee(
                    id=raw_employee['id'],
                    last_name=raw_employee['surname'],
                    first_name=raw_employee['name'],
                    middle_name='',
                    department=raw_employee['department'],
                    admin=raw_employee['admin'],
                    head=raw_employee['head'],
                    bitrix_id=raw_employee['bitrix_id']
                ))
        else:
            return None
        
        return employees if all else employees[0]

    async def get_employee_worktime(self, employee_id: int, date: date = None, last: bool = False) -> EmployeesWorktime | None:
        sql = (
            'select * from employees_worktime '
            'where employee_id = %(employee_id)s and '
        )

        if last:
            sql += 'start_time = (select max(start_time) from employees_worktime where employee_id = %(employee_id)s)'
        else:
            sql += "date_trunc('day', start_time) = %(date)s"

        employee_worktime = await self._make_base_query(
            sql=sql,
            data={'employee_id': employee_id, 'date': date}
        )

        if employee_worktime:
            return EmployeesWorktime(
                employee_id=employee_worktime['employee_id'],
                start_time=employee_worktime['start_time'],
                end_time=employee_worktime['end_time']
            )
        else:
            return None
        
    
    async def get_employee_schedule(self, employee_id: int, today: bool = False, last: bool = False, date_start: date = None, days: timedelta = timedelta(days=1)):
        employee_schedule = []
        
        sql = (
            'select * from employees_schedule '
            'where employee_id = %(employee_id)s and '
        )
        data = {'employee_id': employee_id}

        if today:
            sql += "date_trunc('day', start_datetime) = %(today_date)s"
            data += {'today_date': datetime.now().date()}
            fetch_all = False

        elif last:
            sql += 'start_datetime = (select max(start_datetime) from employees_schedule where employee_id = %(employee_id)s)'
            fetch_all = False

        
        elif date_start is not None:
            sql += 'start_datetime between %(date_start)s and %(date_end)s'
            data += {'date_start': date_start, 'date_end': date_start + days}
            fetch_all = True

        
        else:
            return False
        
        raw_employee_schedules = await self._make_base_query(
            sql=sql,
            data=data,
            fetch_all=fetch_all
        )

        if raw_employee_schedules:
            if isinstance(raw_employee_schedules, dict):
                raw_employee_schedules = [raw_employee_schedules]
                for raw_employee_schedule in raw_employee_schedules:
                    employee_schedule.append(EmployeeSchedule(
                        employee_id = raw_employee_schedule['employee_id'],
                        start_datetime=raw_employee_schedule['start_datetime'],
                        end_datetime=raw_employee_schedule['end_datetime']
                    )
                )
        else:
            return None
        
        return employee_schedule if fetch_all else employee_schedule[0]



         
    async def insert_employee_start_work_info(self, employees_worktime: EmployeesWorktime):
        last_start_work_time = await self.get_employee_worktime(employees_worktime.employee_id, last=True)
        
        if last_start_work_time is not None:
#           # Проверяем, не начат ли УЖЕ в этот день рабочий день
            if last_start_work_time.start_time.date() == employees_worktime.start_time.date():
                return False

        return await self._make_base_query(
            sql='insert into employees_worktime (employee_id, start_time) values (%(employee_id)s, %(start_time)s)',
            data={'employee_id': employees_worktime.employee_id, 'start_time': employees_worktime.start_time},
            commit_needed=True
        )

    async def insert_employee_end_work_info(self, employees_worktime: EmployeesWorktime):
        today_worktime = await self.get_employee_worktime(employee_id=employees_worktime.employee_id, date=datetime.now().date())
        
        if today_worktime is not None:
            # Проверяем, не закончен ли УЖЕ в этот день рабочий день
            if today_worktime.end_time is not None:
                raise Exception('WorkdayAlreadyEnded')
            
            return await self._make_base_query(
                sql='update employees_worktime set end_time = %(end_time)s where employee_id = %(employee_id)s and start_time = %(start_time)s',
                data={'employee_id': employees_worktime.employee_id, 'end_time': employees_worktime.end_time, 'start_time': today_worktime.start_time},
                commit_needed=True
            ), today_worktime.start_time
            
        else:
            raise Exception('WorkdayNotStarted') # Вызываем ошибку о еще не начатом рабочем дне
        


            
        


        
            
        

async def start():
    db = Database(on_error_callback=lambda error, sql, data, caller_function_name: print('PostgreSQL: ', error))
    await db.login()
    print(await db.get_employee_worktime(employee_id=5163143779, date=datetime(year=2024, month=7, day=18).date()))


if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(start())

