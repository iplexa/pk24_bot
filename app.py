from flask import Flask, request, jsonify, render_template
import sqlite3
import telebot

app = Flask(__name__)

TOKEN = '7435101532:AAEEwhIHRPEGEnWNGDdydyE740XjWrSsuXg'
GENERIC_CHAT = -4212167319
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# SQLite database connection
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

# Authorization credentials
username = 'Сотрудник_ПК24'
password = 'rfvtgb'

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        if login == username and password == password:
            # Authorized, redirect to index
            return render_template('index.html')
        else:
            # Invalid credentials, display error message
            bot.send_message(GENERIC_CHAT, 'пидоры зайти пытаются')
            return 'Invalid login or password', 401
    return render_template('login.html')

@app.route('/index', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/applications', methods=['GET'])
def applications():
    cursor.execute("""
        select
            a.id as '#',
            case
            when a.applicant_patronymic != '' then a.applicant_surname || ' ' || a.applicant_name || ' ' || a.applicant_patronymic
            when a.applicant_patronymic = '' then a.applicant_surname || ' ' || a.applicant_name
            end as 'ФИО',
            e.name || ' ' ||  e.surname as 'ФИО сотрудника',
            a.status as 'Статус заявления в ПК',
            a.reason as 'Причина отказа',
            a.datetime as 'Дата проверки'
        from applications a
        left join employees e on a.employee_id = e.id
    """)
    results = cursor.fetchall()
    return render_template('applications.html', results=results)

@app.route('/worktime', methods=['GET', 'POST'])
def worktime():
    cursor.execute("""
        SELECT 
            ew.id,
            e.name || ' ' || e.surname AS 'ФИО сотрудника',
            e.department,
            ew.workday,
            ew.starttime,
            ew.endtime
        FROM employees_worktime ew
        JOIN employees e ON ew.employee_id = e.id
    """)
    results = cursor.fetchall()
    return render_template('worktime.html', results=results)

@app.route('/employees', methods=['GET'])
def emloyees():
    cursor.execute("""
        SELECT
            e.id,
            e.name || ' ' || e.surname AS 'ФИО',
            e.department
        FROM employees e
    """)
    results = cursor.fetchall()
    return render_template('employees.html', results=results)


if __name__ == '__main__':
    app.run(host='192.168.1.62')