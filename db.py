# Database Class

import sqlite3
import psycopg2
import inspect

from datetime import datetime, timedelta

import psycopg2.extras


class Database:
    def __init__(self, db_file_path: str, on_error_callback: callable) -> None:
        # self._db = sqlite3.connect(database=db_file_path, check_same_thread=False)
        self._db = psycopg2.connect(
            dbname="pk24",
            user="serviceskmpo",
            password="Kameta2013!",
            host="77.232.135.162",
            port="5432",
            connection_factory=psycopg2.extras.RealDictConnection
        )
        self.on_error_callback = on_error_callback

    def close(self):
        self._db.close()

    def _make_base_query(self, sql: str, data: tuple = (), fetch_one: bool = True, commit_needed: bool = False, on_error_callback: callable = None):
        cursor = self._db.cursor()

        try:
            cursor.execute(sql, data)
            # raise sqlite3.Error('Тест ошибки')

            if commit_needed:
                self._db.commit()
                return True
            else:    
                if fetch_one:
                    return cursor.fetchone()
                else:
                    return cursor.fetchall()
        except psycopg2.Error as error:
            self._db.rollback()
            caller_function_name = inspect.stack()[1][0].f_code.co_name

            if on_error_callback is None:
                self.on_error_callback(error, sql, data, caller_function_name)
            else:
                on_error_callback(error, sql, data, caller_function_name)

            return False
        finally:
            cursor.close()
    
    def get_employee_department(self, employee_id: int):
        return self._make_base_query(
            sql='select department from employees where id = %s',
            data=(employee_id,)
        )
    
    def get_employee_data(self, employee_id: int):
        return self._make_base_query(
            sql="select *, concat_ws(' ', name, surname) as fullname from employees where id = %s",
            data=(employee_id,)
        )
    
    def register_employee(self, employee_id, employee_name, employee_surname, employee_department):
        return self._make_base_query(
            sql='insert into employees (id, name, surname, department) values (%s,%s,%s,%s)',
            data=(employee_id, employee_name, employee_surname, employee_department),
            commit_needed=True
        )

    def start_employee_work(self, employee_id, start_time: int) -> bool:
        start_time_already_exist = self._make_base_query(
            sql='select start_time from employees_worktime where employee_id = %s and start_time = (select max(start_time) from employees_worktime where employee_id = %s)',
            data=(employee_id, employee_id)
        )

        if start_time_already_exist is not None:
            # Проверяем, не начат ли УЖЕ в этот день рабочий день
            if start_time_already_exist['start_time'].date() == datetime.fromtimestamp(start_time).date():
                return False
        
        return self._make_base_query(
            sql='insert into employees_worktime (employee_id, start_time) values (%s,%s)',
            data=(employee_id, datetime.fromtimestamp(start_time)),
            commit_needed=True
        )
     
    def get_employee_workday_information(self, employee_id, workday):
        return self._make_base_query(
            sql='select * from employees_worktime where employee_id = %s and start_time between %s and %s',
            data=(employee_id, datetime.fromtimestamp(workday), datetime.fromtimestamp(workday+86400))
            )
    
    def get_employees_schedule_via_date(self, workday):
        return self._make_base_query(
            sql="select ed.employee_id, ed.start_datetime, ed.end_datetime, e.department, CONCAT_WS(' ', e.name, e.surname) as employee_fullname from employees_schedule ed left join employees e on e.id = ed.employee_id where start_datetime between %s and %s ORDER BY department DESC",
            data=(workday, workday+86400),
            fetch_one=False
        )
    
    def get_employess_whose_schedule_not_filled(self, workday):
        return self._make_base_query(
            sql="SELECT id, concat_ws(' ', name, surname) as employee_fullname, department FROM employees WHERE NOT EXISTS (SELECT 1 FROM employees_schedule WHERE employee_id = employees.id AND start_datetime between %s and %s) ORDER BY department DESC",
            data=(workday, workday+86400),
            fetch_one=False 
        )



    def end_employee_work(self, employee_id, end_time):
        end_time_already_exist = self._make_base_query(
            sql='select end_time from employees_worktime where employee_id = %s and end_time = (select max(end_time) from employees_worktime where employee_id = %s)',
            data=(employee_id, employee_id)
        )

        # Проверяем, начат ли в этот день рабочий день
        today = datetime.fromtimestamp(end_time)
        today_date = today.replace(hour = 0, minute = 0, second = 0, microsecond = 0).timestamp()
        is_workday_started = self.get_employee_workday_information(
            employee_id=employee_id,
            workday = today_date
        )
        
        if is_workday_started:
            if end_time_already_exist is not None:
                # Проверяем, не закончен ли УЖЕ в этот день рабочий день
                
                if end_time_already_exist['end_time'].date() == datetime.fromtimestamp(end_time).date():
                    return False, None, None
            
            return self._make_base_query(
                sql='''
                UPDATE employees_worktime
                SET end_time = %s
                WHERE employee_id = %s AND start_time = %s
                ''',
                data=(datetime.fromtimestamp(end_time), employee_id, is_workday_started['start_time']),
                commit_needed=True
            ), is_workday_started['start_time'], end_time 

    def send_online_application(self, snils: int | str, applicant_name: str, applicant_surname: str, applicant_patronymic: str, employee_id: int, status: str, deny_reason, datetime: int, is_spo: bool = False):
        return self._make_base_query(
            sql=f'INSERT INTO applications ({"spo_number" if is_spo else "snils"}, applicant_name, applicant_surname, applicant_patronymic, employee_id, status, deny_reason, submit_method, datetime) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
            data=(snils, applicant_name, applicant_surname, applicant_patronymic, employee_id, True if status == 'Принято' else False, deny_reason, 'Онлайн', datetime),
            commit_needed=True
        )
    
    def send_person_applicate(self, snils: int | str, applicant_name: str, applicant_surname: str, applicant_patronymic: str, employee_id: int, passed_original_certificate: int, datetime: int, is_spo: bool = False):
        return self._make_base_query(
            sql=f'INSERT INTO applications ({"spo_number" if is_spo else "snils"}, applicant_name, applicant_surname, applicant_patronymic, employee_id, status, passed_original_certificate, datetime, submit_method) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
            data=(snils, applicant_name, applicant_surname, applicant_patronymic, employee_id, True, bool(passed_original_certificate), datetime, 'Очно'),
            commit_needed=True
        )
    
    def find_application_info(self, find_data, find_by_snils: bool = False):
        return self._make_base_query(
            sql=f"""
                SELECT CONCAT_WS(' ', applicant_surname, applicant_name, applicant_patronymic) as fullname, *, CONCAT_WS(' ', e.name, e.surname) as employee_fullname
                FROM applications
                left join employees e on employee_id = e.id
                WHERE {'snils = %s' if find_by_snils else "CONCAT_WS(' ', applicant_surname, applicant_name, applicant_patronymic) LIKE %s"}
            """,
            data = (int(find_data),) if find_by_snils else ("%"+find_data+"%",),
            fetch_one=False
        )
    
    def get_applicant_data_via_snils(self, applicant_snils: int | str, is_spo: bool = False):
        return self._make_base_query(
            sql=f"SELECT a.*, CONCAT_WS(' ', e.name, e.surname) as employee_fullname from applications a left join employees e on employee_id = e.id where {'snils = %s' if not is_spo else 'spo_number = %s'} and status = true and datetime = (select max(datetime) from applications where {'snils = %s' if not is_spo else 'spo_number = %s'}) limit 1",
            data=(applicant_snils, applicant_snils)
        )
    
    def get_applicant_data_via_id(self, application_id: int):
        return self._make_base_query(
            sql='SELECT * from applications where id = %s',
            data=(application_id,)
        )
    
    def get_applicant_fullname_via_id(self, application_id: int):
        print(application_id)
        return self._make_base_query(
            sql="SELECT case when applicant_patronymic != '' then CONCAT_WS(' ', applicant_surname, applicant_name, applicant_patronymic) when applicant_patronymic = '' then CONCAT_WS(' ', applicant_surname, applicant_name) end as applicant_fullname from applications where id = %s",
            data=(application_id,)
        )
    
    def send_info_about_passed_original_certificate(self, applicantion_id: int, passed_original_certificate_status: int, responsible_employee_id: int):
        return self._make_base_query(
            sql='update applications set passed_original_certificate = %s, responsible_employee_id = %s where id = %s',
            data=(bool(passed_original_certificate_status), responsible_employee_id, applicantion_id),
            commit_needed=True
        )

    def send_check_application_file(self, otk_employee_id: int, has_errors_otk, datetime_otk_check, application_id: int, errors_otk: str = ''):
        return self._make_base_query(
            sql='update applications set employee_otk_id = %s, status_otk = %s, has_errors_otk = %s, errors_otk = %s, datetime_otk_check = %s where id = %s',
            data=(otk_employee_id, True, bool(has_errors_otk), errors_otk, datetime_otk_check, application_id),
            commit_needed=True
        )


    def fill_schedule(self, employee_id: int, start_date: datetime, worktime: list, is_saturday: bool):
        start_datetime_first = (start_date + timedelta(hours=worktime[0], minutes=worktime[1])).timestamp()
        end_datetime_first = (start_date + timedelta(hours=worktime[2], minutes=worktime[3])).timestamp()

        for i in range(5): 
            if self._make_base_query(
                sql='insert into employees_schedule (employee_id, start_datetime, end_datetime) values (%s,%s,%s)',
                data=(employee_id, start_datetime_first, end_datetime_first),
                commit_needed=True
            ):
                start_datetime_first += 86400
                end_datetime_first += 86400
            else:
                return False
        if is_saturday:
            saturday_start = (start_date + timedelta(days=5, hours=10)).timestamp()
            saturday_end = saturday_start + 21600
            
            if not self._make_base_query(
                sql='insert into employees_schedule (employee_id, start_datetime, end_datetime) values (%s,%s,%s)',
                data=(employee_id, saturday_start, saturday_end),
                commit_needed=True
            ):
                return False
        return True
    
    def change_schedule(self, employee_id: int, start_date: datetime, worktime: list):
        day = start_date.timestamp()
        start_datetime = (start_date + timedelta(hours=worktime[0], minutes=worktime[1])).timestamp()
        end_datetime = (start_date + timedelta(hours=worktime[2], minutes=worktime[3])).timestamp()

        return self._make_base_query(
            sql='UPDATE employees_schedule set start_datetime = %s, end_datetime = %s where employee_id = %s and start_datetime between %s and %s',
            data=(start_datetime, end_datetime, employee_id, day, day+86400),
            commit_needed=True
        )


    def get_last_employee_workday_in_schedule(self, employee_id: int):
        return self._make_base_query(
            sql='select end_datetime from employees_schedule where employee_id = %s and end_datetime = (select max(end_datetime) from employees_schedule where employee_id = %s)',
            data=(employee_id,employee_id)
        )
            
    def get_employee_schedule_via_startdate(self, employee_id: int, startdate: datetime):
        startdate_int = startdate.timestamp()
        return self._make_base_query(
            sql='select start_datetime, end_datetime from employees_schedule where employee_id = %s and start_datetime between %s and %s',
            data=(employee_id, startdate_int, startdate_int + 604800),
            fetch_one=False
        )

    def get_employee_schedule_information(self, employee_id: int, workday: datetime):
        workday_int = workday.timestamp()
        return self._make_base_query(
            sql='select start_datetime, end_datetime from employees_schedule where employee_id = %s and start_datetime between %s and %s',
            data=(employee_id, workday_int, workday_int + 86400)
        )
        
    def get_employees_via_department(self, employees_department: str):
        return self._make_base_query(
            sql="select CONCAT_WS(' ', name, surname) as fullname, id from employees where department = %s",
            data=(employees_department,),
            fetch_one=False
        )
    
    def get_employees_have_bitrix(self):
        return self._make_base_query(
            sql="select id, concat_ws(' ', name, surname) as fullname from employees where bitrix_id is not null",
            data=(),
            fetch_one=False
        )

    def get_employee_data_via_fullname(self, employee_fullname: str):
        employee_fullname_list = employee_fullname.rsplit(maxsplit=1)

        return self._make_base_query(
            sql='select * from employees where name = %s and surname = %s',
            data=(employee_fullname_list[0], employee_fullname_list[1])
        )

    def get_daytime_applications_via_employee_id(self, employee_id: int, date: datetime, is_otk: bool = False):
        date_int = date.timestamp()
        return self._make_base_query(
            sql=f'select count(*) as "applications_count" from applications where {"employee_otk_id" if is_otk else "employee_id"} = %s and {"datetime_otk_check" if is_otk else "datetime"} between %s and %s',
            data=(employee_id, date_int, date_int + 86400)
        )
    
    def get_daytime_processed_applications_via_employee_id(self, employee_id: int, date: datetime):
        date_int = date.timestamp()
        return self._make_base_query(
            sql='select count(*) as "applications_count" from applications where employee_otk_id = %s and datetime_otk_check between %s and %s',
            data=(employee_id, date_int, date_int + 86400)
        )
    
    def get_daytime_calls_via_employee_id(self, employee_id: int, date: datetime):
        date_int = date.timestamp()
        return self._make_base_query(
            sql='select count(*) as "calls_count" from calls where employee_id_start = %s and datetime between %s and %s',
            data=(employee_id, date_int, date_int + 86400)
        )

    def get_daytime_work_count(self, department, date: datetime):
        date_int = date.timestamp()
        match(department):
            case('ОТК'):
                return self._make_base_query(
                    sql='select count(*) as applications_count from applications where datetime_otk_check between %s and %s',
                    data=(date_int, date_int + 86400)
                )
            case('FrontLine'):
                return self._make_base_query(
                    sql=f"select count(*) as applications_count from applications where submit_method = 'Очно' and datetime between %s and %s",
                    data=(date_int, date_int + 86400)
                )
            case('Онлайн-заявления'):
                return self._make_base_query(
                    sql=f"select count(*) as applications_count from applications where submit_method = 'Онлайн' and datetime between %s and %s",
                    data=(date_int, date_int + 86400)
                )
            case('CallCentre'):
                return self._make_base_query(
                    sql='select count(*) as calls_count from calls where datetime between %s and %s',
                    data=(date_int, date_int + 86400)
                )



    def get_employee_via_bitrix_id(self, bitrix_id: int): 
        return self._make_base_query(
            sql="select id, department, CONCAT_WS(' ', name, surname) as employee_fullname from employees where bitrix_id = %s",
            data=(bitrix_id,)
        )
    
    def get_employee_via_call_id(self, call_id: str):
        return self._make_base_query(
            sql="select e.*, CONCAT_WS(' ', e.name, e.surname) as employee_fullname from calls left join employees e on e.id = employee_id_start where call_id = %s",
            data=(call_id,),
        )

    def send_call_on_start(self, call_id: str, employee_id_start: int):
        return self._make_base_query(
            sql='insert into calls (call_id, employee_id_start) values (%s,%s)',
            data=(call_id, employee_id_start),
            commit_needed=True
        )
    
    def send_call_on_end(self, call_id: str, employee_id_end: int, phone_number: int, call_duration: int, call_start_date: int):
        return self._make_base_query(
            sql='update calls set employee_id_end = %s, phone_number = %s, call_duration = %s, datetime = %s where call_id = %s',
            data=(employee_id_end, phone_number, call_duration, call_start_date, call_id),
            commit_needed=True
        )

    def is_emloyee_has_permission(self, employee_id: int, permissions: list) -> bool:
        employee = self.get_employee_data(employee_id=employee_id)
        
        if employee['admin']:
            return True
        
        if employee['department'] in permissions:
            return True
        else:
            return False

    def is_head(self, employee_id: int) -> bool:
        employee = self.get_employee_data(employee_id=employee_id)
        
        if employee['head']:
            return True
        else:
            return False

    def is_admin(self, employee_id: int) -> bool:
        employee = self.get_employee_data(employee_id=employee_id)

        if employee['admin']:
            return True
        else:
            return False
        
    def get_employees_schedule(self):
        return self._make_base_query(
            sql='SELECT employee_id, start_datetime, end_datetime FROM employees_schedule',
            data=(),
            fetch_one=False
        )
    
    def get_employees(self):
        return self._make_base_query(
            sql = "SELECT employee_id, contact_ws(' ', name, surname) FROM employees"
        )
       