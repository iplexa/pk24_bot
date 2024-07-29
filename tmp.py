from datetime import datetime, timezone, timedelta


# with open(file='start_time.txt', mode='r', encoding='utf-8') as start_file:
#     with open(file='iso_start.txt', mode='w', encoding='utf-8') as iso_start_file:
#         for start_line in start_file.readlines():
#             date_iso_format = datetime.fromtimestamp(int(start_line.strip()), tz=timezone(offset=timedelta(hours=3)))
#             iso_start_file.write(f'{date_iso_format.isoformat(sep=' ')}\n')

with open(file='start_time.txt', mode='r', encoding='utf-8') as end_file:
    with open(file='iso_start.txt', mode='w', encoding='utf-8') as iso_end_file:
        for end_line in end_file.readlines():
            if end_line.strip() == '':
                iso_end_file.write('\n')
            else:
                date_iso_format = datetime.fromtimestamp(int(end_line.strip()), tz=timezone(offset=timedelta(hours=3)))
                iso_end_file.write(f'{date_iso_format.isoformat(sep=' ')}\n')

# class Foo:
#     def __init__(self) -> None:
#         self.var = 'Москва'
    
#     @property
#     def now(self) -> datetime:
#         return datetime.now()

# print(Foo().now)