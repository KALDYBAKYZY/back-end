from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from datetime import datetime, date, time, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from sqlalchemy import CheckConstraint, UniqueConstraint, text
import os
from werkzeug.security import generate_password_hash
import re
import bcrypt

print("Current working directory:", os.getcwd())
print("Template folder path:", os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates')))
app = Flask(__name__, template_folder='html2')
app.secret_key = 'your_secret_key'  # В продакшене замените на безопасный ключ

# Конфигурация базы данных
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:12345678@localhost:5433/FinalProj"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SESSION_TYPE'] = 'sqlalchemy'

db = SQLAlchemy(app)
app.config['SESSION_SQLALCHEMY'] = db
Session(app)

# Модели SQLAlchemy
class Clients(db.Model):
    __tablename__ = 'clients'
    clientid = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(50))
    lastname = db.Column(db.String(50))
    phonenumber = db.Column(db.String(17))
    password = db.Column(db.String(8))
    dob = db.Column(db.Date)
    medicalrecords = db.Column(db.Text)
    __table_args__ = (
        UniqueConstraint('clientid', 'phonenumber', name='Unique_ClientID_PhoneNumber'),
    )

class Classes(db.Model):
    __tablename__ = 'classes'
    classid = db.Column(db.Integer, primary_key=True)
    classname = db.Column(db.String(100))
    trainerid = db.Column(db.Integer, db.ForeignKey('trainers.trainerid'))
    classtime = db.Column(db.Time)
    classdate = db.Column(db.Date)
    duration = db.Column(db.Integer)
    maxparticipants = db.Column(db.Integer)

class ClientClasses(db.Model):
    __tablename__ = 'clientclasses'
    clientid = db.Column(db.Integer, db.ForeignKey('clients.clientid', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    classid = db.Column(db.Integer, db.ForeignKey('classes.classid', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

class Trainers(db.Model):
    __tablename__ = 'trainers'
    trainerid = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(50))
    lastname = db.Column(db.String(50))
    specialty = db.Column(db.String(100))
    phonenumber = db.Column(db.String(15), unique=True)
    password = db.Column(db.String(6))
    locationid = db.Column(db.Integer, db.ForeignKey('locations.locationid'))
    dob = db.Column(db.Date)
    experience = db.Column(db.Integer)

class TrainersClasses(db.Model):
    __tablename__ = 'trainersclasses'
    trainerid = db.Column(db.Integer, db.ForeignKey('trainers.trainerid', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    classid = db.Column(db.Integer, db.ForeignKey('classes.classid', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

class MembershipTypes(db.Model):
    __tablename__ = 'membershiptypes'
    membershiptypeid = db.Column(db.Integer, primary_key=True)
    typename = db.Column(db.String(50))
    price = db.Column(db.Numeric(10, 2))
    durationmonths = db.Column(db.Integer)
    __table_args__ = (
        CheckConstraint('price > 0', name='Check_price'),
    )

class Memberships(db.Model):
    __tablename__ = 'memberships'
    membershipid = db.Column(db.Integer, primary_key=True)
    clientid = db.Column(db.Integer, db.ForeignKey('clients.clientid', ondelete='CASCADE'))
    membershiptypeid = db.Column(db.Integer, db.ForeignKey('membershiptypes.membershiptypeid'))
    startdate = db.Column(db.Date, default=db.func.current_date())
    enddate = db.Column(db.Date)

class Payments(db.Model):
    __tablename__ = 'payments'
    paymentid = db.Column(db.Integer, primary_key=True)
    clientid = db.Column(db.Integer, db.ForeignKey('clients.clientid', ondelete='CASCADE'))
    membershipid = db.Column(db.Integer, db.ForeignKey('memberships.membershipid'))
    amount = db.Column(db.Numeric(10, 2))
    paymentdate = db.Column(db.Date, default=db.func.current_date())

class Schedule(db.Model):
    __tablename__ = 'schedule'
    scheduleid = db.Column(db.Integer, primary_key=True)
    trainerid = db.Column(db.Integer, db.ForeignKey('trainers.trainerid', ondelete='CASCADE'))
    clientid = db.Column(db.Integer, db.ForeignKey('clients.clientid', ondelete='SET NULL'))
    trainingdate = db.Column(db.Date, nullable=False)
    trainingtime = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='Свободно')
    locationid = db.Column(db.Integer, db.ForeignKey('locations.locationid'))
    __table_args__ = (
        CheckConstraint("status IN ('Свободно', 'Занято')"),
    )

class Assignments(db.Model):
    __tablename__ = 'assignments'
    assignmentid = db.Column(db.Integer, primary_key=True)
    trainerid = db.Column(db.Integer, db.ForeignKey('trainers.trainerid'))
    clientid = db.Column(db.Integer, db.ForeignKey('clients.clientid'))
    tasktext = db.Column(db.Text, nullable=False)
    duedate = db.Column(db.Date, nullable=False)
    iscompleted = db.Column(db.Boolean, default=False)

class Achievements(db.Model):
    __tablename__ = 'achievements'
    achievementid = db.Column(db.Integer, primary_key=True)
    clientid = db.Column(db.Integer, db.ForeignKey('clients.clientid', ondelete='CASCADE'))
    achievementname = db.Column(db.String(50), nullable=False)
    dateearned = db.Column(db.Date, default=db.func.current_date())
    __table_args__ = (
        UniqueConstraint('clientid', 'achievementname'),
    )

class Locations(db.Model):
    __tablename__ = 'locations'
    locationid = db.Column(db.Integer, primary_key=True)
    locationname = db.Column(db.String(100), unique=True)

# Маршрут для рендеринга страницы логина
@app.route('/')
def home():
    print("Маршрут '/' вызван")
    if 'role' in session:
        print(f"Роль в сессии: {session['role']}")
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif session['role'] == 'trainer':
            return redirect(url_for('trainer_dashboard'))
        elif session['role'] == 'client':
            return redirect(url_for('client_dashboard'))
    print("Рендеринг login.html")
    return render_template('login.html')

# Маршрут для страницы регистрации
@app.route('/register')
def register_page():
    return render_template('register.html')

# Маршрут для страницы администратора
@app.route('/admin')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('home'))
    return render_template('admin.html')

# Маршрут для страницы тренера
@app.route('/trainer')
def trainer_dashboard():
    if 'role' not in session or session['role'] != 'trainer':
        return redirect(url_for('home'))
    return render_template('trainer.html', trainer_id=session.get('trainerid'))

# Маршрут для страницы клиента
@app.route('/client')
def client_dashboard():
    if 'role' not in session or session['role'] != 'client':
        return redirect(url_for('home'))
    return render_template('client.html', client_id=session.get('clientid'))

# Маршрут для выхода
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Маршрут для логина
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    surname = data.get('surname')
    name = data.get('name')
    password = data.get('password')

    if not surname or not name or not password:
        return jsonify({'error': 'Заполните все поля!'}), 400

    # Проверка на администратора
    if surname == "Database" and name == "Fitnes" and password == "123456":
        session['role'] = 'admin'
        return jsonify({'message': 'Вход выполнен как Администратор!', 'role': 'admin'})

    try:
        # Проверка тренера
        trainer = Trainers.query.filter_by(lastname=surname, firstname=name).first()
        if trainer and bcrypt.checkpw(password.encode('utf-8'), trainer.password.encode('utf-8')):
            session['role'] = 'trainer'
            session['trainerid'] = trainer.trainerid
            return jsonify({
                'message': 'Вход выполнен как Тренер!',
                'role': 'trainer',
                'trainerid': trainer.trainerid
            })

        # Проверка клиента
        client = Clients.query.filter_by(lastname=surname, firstname=name).first()
        if client and bcrypt.checkpw(password.encode('utf-8'), client.password.encode('utf-8')):
            session['role'] = 'client'
            session['clientid'] = client.clientid
            return jsonify({
                'message': 'Вход выполнен как Клиент!',
                'role': 'client',
                'clientid': client.clientid
            })

        return jsonify({'error': 'Неверное имя пользователя или пароль!'}), 401
    except Exception as e:
        return jsonify({'error': f'Ошибка доступа к БД: {str(e)}'}), 500

#register
@app.route('/register', methods=['POST'])
def register():
    try:
        # Получаем данные из запроса
        data = request.json
        firstname = data.get('firstname')
        lastname = data.get('lastname')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        phonenumber = data.get('phonenumber')
        dob = data.get('dob')
        role = data.get('role')  # Роль может быть 'trainer' или 'client'

        # Проверка, чтобы все поля были заполнены
        if not firstname or not lastname or not password or not confirm_password or not phonenumber or not dob or not role:
            return jsonify({'error': 'Заполните все поля!'}), 400

        # Проверка на совпадение паролей
        if password != confirm_password:
            return jsonify({'error': 'Пароли не совпадают!'}), 400

        # Проверка на правильность формата телефонного номера
        phone_regex = r'^\+?[0-9]{10,15}$'  # Убедитесь, что формат телефона соответствует требованиям
        if not re.match(phone_regex, phonenumber):
            return jsonify({'error': 'Неверный формат телефонного номера!'}), 400

        # Хеширование пароля с использованием bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        if role == 'trainer':
            # Проверка на существующего тренера по телефону
            existing_trainer = Trainers.query.filter_by(phonenumber=phonenumber).first()
            if existing_trainer:
                return jsonify({'error': 'Тренер с таким номером телефона уже существует!'}), 400

            # Добавление нового тренера в базу данных
            new_trainer = Trainers(
                firstname=firstname,
                lastname=lastname,
                password=hashed_password.decode('utf-8'),
                phonenumber=phonenumber,
                dob=dob
            )
            db.session.add(new_trainer)
            db.session.commit()

            return jsonify({'message': 'Регистрация тренера успешна!'}), 201

        elif role == 'client':
            # Проверка на существующего клиента по телефону
            existing_client = Clients.query.filter_by(phonenumber=phonenumber).first()
            if existing_client:
                return jsonify({'error': 'Клиент с таким номером телефона уже существует!'}), 400

            # Добавление нового клиента в базу данных
            new_client = Clients(
                firstname=firstname,
                lastname=lastname,
                password=hashed_password.decode('utf-8'),
                phonenumber=phonenumber,
                dob=dob
            )
            db.session.add(new_client)
            db.session.commit()

            return jsonify({'message': 'Регистрация клиента успешна!'}), 201

        else:
            return jsonify({'error': 'Некорректная роль пользователя!'}), 400

    except Exception as e:
        app.logger.error(f"Ошибка при регистрации: {str(e)}")
        return jsonify({'error': f'Ошибка при регистрации: {str(e)}'}), 500

# Маршрут для отображения таблицы
@app.route('/table/<string:table_name>', methods=['GET'])
def display_table(table_name):
    table_name = table_name.lower()
    allowed_tables = {
        'clients': Clients,
        'trainers': Trainers,
        'classes': Classes,
        'clientclasses': ClientClasses,
        'trainersclasses': TrainersClasses,
        'membershiptypes': MembershipTypes,
        'memberships': Memberships,
        'payments': Payments,
        'schedule': Schedule,
        'assignments': Assignments
    }

    if table_name not in allowed_tables:
        return jsonify({'error': f'Таблица "{table_name}" не найдена'}), 404

    try:
        # Получаем модель таблицы
        model = allowed_tables[table_name]
        # Выполняем запрос через ORM
        rows = model.query.all()

        # Преобразуем данные в словарь
        result_data = []
        for row in rows:
            row_dict = {}
            for column in row.__table__.columns:
                value = getattr(row, column.name)
                if isinstance(value, date):
                    row_dict[column.name] = value.isoformat()
                elif isinstance(value, time):
                    row_dict[column.name] = value.isoformat()
                else:
                    row_dict[column.name] = value
            result_data.append(row_dict)

        return jsonify(result_data)
    except Exception as e:
        print(f"Ошибка в display_table для таблицы {table_name}: {str(e)}")
        return jsonify({'error': f'Не удалось загрузить таблицу: {str(e)}'}), 500

# Маршрут для добавления клиента
@app.route('/add_client', methods=['POST'])
def add_client():
    data = request.json
    client_id = data.get('client_id')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    phone = data.get('phone')
    password = data.get('password')
    dob = data.get('DataOfBirthday')
    medicalrecords = data.get('medicalrecords')

    if not client_id or not first_name or not last_name or not phone or not password:
        return jsonify({'error': 'Все поля должны быть заполнены!'}), 400

    try:
        new_client = Clients(
            clientid=client_id,
            firstname=first_name,
            lastname=last_name,
            phonenumber=phone,
            password=password,
            dob=dob,
            medicalrecords=medicalrecords
        )
        db.session.add(new_client)
        db.session.commit()
        return jsonify({'message': 'Клиент успешно добавлен!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Не удалось добавить клиента: {str(e)}'}), 500

# Маршрут для обновления клиента
@app.route('/update_client', methods=['POST'])
def update_client():
    data = request.json
    client_id = data.get('client_id')
    new_first_name = data.get('new_first_name')
    new_last_name = data.get('new_last_name')
    new_phone = data.get('new_phone')
    new_password = data.get('new_password')

    if not client_id:
        return jsonify({'error': 'Введите ID клиента для обновления!'}), 400

    if not new_first_name and not new_last_name and not new_phone and not new_password:
        return jsonify({'error': 'Введите хотя бы одно поле для обновления!'}), 400

    try:
        client = Clients.query.get(client_id)
        if not client:
            return jsonify({'error': 'Клиент не найден!'}), 404

        if new_first_name:
            client.firstname = new_first_name
        if new_last_name:
            client.lastname = new_last_name
        if new_phone:
            client.phonenumber = new_phone
        if new_password:
            client.password = new_password

        db.session.commit()
        return jsonify({'message': 'Данные клиента успешно обновлены!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Не удалось обновить данные клиента: {str(e)}'}), 500

# Маршрут для удаления клиента
@app.route('/delete_client', methods=['POST'])
def delete_client():
    data = request.json
    client_id = data.get('client_id')

    if not client_id:
        return jsonify({'error': 'Введите ID клиента для удаления!'}), 400

    try:
        client = Clients.query.get(client_id)
        if not client:
            return jsonify({'error': 'Клиент не найден!'}), 404

        db.session.delete(client)
        db.session.commit()
        return jsonify({'message': 'Клиент успешно удален!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Не удалось удалить клиента: {str(e)}'}), 500

# Маршрут для получения тренеров по занятию
@app.route('/trainers_for_class', methods=['POST'])
def trainers_for_class():
    data = request.json
    class_name = data.get('class_name')

    if not class_name:
        return jsonify({'error': 'Выберите название занятия!'}), 400

    try:
        trainers = db.session.query(Trainers).join(Classes).filter(Classes.classname == class_name).all()
        result = [
            {
                'ID': trainer.trainerid,
                'FirstName': trainer.firstname,
                'LastName': trainer.lastname,
                'Specialty': trainer.specialty
            }
            for trainer in trainers
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Не удалось получить данные: {str(e)}'}), 500

# Маршрут для получения средней цены абонементов
@app.route('/avg_price', methods=['GET'])
def avg_price():
    try:
        average_price = db.session.query(db.func.avg(MembershipTypes.price)).scalar()
        if average_price:
            average_price = round(float(average_price), 2)
            return jsonify({'average_price': average_price})
        return jsonify({'average_price': None})
    except Exception as e:
        return jsonify({'error': f'Не удалось получить данные: {str(e)}'}), 500

# Маршрут для поиска абонементов по имени
@app.route('/search_type', methods=['POST'])
def search_type():
    data = request.json
    search_name = data.get('search_name')

    if not search_name:
        return jsonify({'error': 'Выберите название абонемента!'}), 400

    try:
        memberships = MembershipTypes.query.filter(MembershipTypes.typename.ilike(f'%{search_name}%')).all()
        result = [
            {
                'ID': m.membershiptypeid,
                'Name': m.typename,
                'Price': float(m.price),
                'DurationMonths': m.durationmonths
            }
            for m in memberships
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Не удалось получить данные: {str(e)}'}), 500

# Маршрут для сортировки абонементов по цене
@app.route('/order_by_asc', methods=['GET'])
def order_by_asc():
    try:
        memberships = MembershipTypes.query.order_by(MembershipTypes.price.asc()).all()
        result = [
            {
                'ID': m.membershiptypeid,
                'Name': m.typename,
                'Price': float(m.price),
                'DurationMonths': m.durationmonths
            }
            for m in memberships
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Не удалось получить данные: {str(e)}'}), 500

# Маршрут для получения списка тренеров
@app.route('/trainers', methods=['GET'])
def get_trainers():
    try:
        trainers = Trainers.query.order_by(Trainers.lastname).all()
        return jsonify([
            {'trainerid': t.trainerid, 'lastname': t.lastname}
            for t in trainers
        ])
    except Exception as e:
        return jsonify({'error': f'Ошибка при загрузке тренеров: {str(e)}'}), 500

# Маршрут для сохранения тренировки
@app.route('/save_training', methods=['POST'])
def save_training():
    data = request.json
    trainer = data.get('trainer')
    date_str = data.get('date')
    timee = data.get('time')
    location = data.get('location')

    if not trainer or not date_str or not timee or not location:
        return jsonify({'error': 'Выберите все параметры!'}), 400

    try:
        date_obj = datetime.strptime(date_str, "%m/%d/%y")
        trainer_id = int(trainer.split(" - ")[0])
        location_id = int(location.split(" - ")[0])

        new_schedule = Schedule(
            trainerid=trainer_id,
            trainingdate=date_obj,
            trainingtime=timee,
            locationid=location_id,
            status='Свободно'
        )
        db.session.add(new_schedule)
        db.session.commit()
        return jsonify({'message': 'Тренировка сохранена!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при сохранении: {str(e)}'}), 500

# Маршрут для получения расписания тренера
@app.route('/show_trainer', methods=['POST'])
def show_trainer():
    data = request.json
    trainer_id = data.get('trainer_id')

    if not trainer_id:
        return jsonify({'error': 'Введите ID тренера!'}), 400

    try:
        schedules = db.session.query(Schedule, Clients, Locations).\
            outerjoin(Clients, Schedule.clientid == Clients.clientid).\
            outerjoin(Locations, Schedule.locationid == Locations.locationid).\
            filter(Schedule.trainerid == trainer_id).\
            order_by(Schedule.trainingdate, Schedule.trainingtime).all()

        result = []
        for schedule, client, location in schedules:
            client_name = f"{client.firstname} {client.lastname}" if client else '—'
            row_dict = {
                'ID': schedule.scheduleid,
                'Дата': schedule.trainingdate.isoformat() if schedule.trainingdate else '—',
                'Время': schedule.trainingtime.isoformat() if schedule.trainingtime else '—',
                'Клиент': client_name,
                'Локация': location.locationname if location else '—'
            }
            result.append(row_dict)
        return jsonify(result)
    except Exception as e:
        print(f"Ошибка в show_trainer: {str(e)}")
        return jsonify({'error': f'Не удалось получить данные: {str(e)}'}), 500

# Маршрут для получения расписания клиента
@app.route('/show_client', methods=['POST'])
def show_client():
    data = request.json
    client_id = data.get('client_id')

    if not client_id:
        return jsonify({'error': 'Введите ID клиента!'}), 400

    try:
        schedules = db.session.query(Schedule, Trainers, Locations).\
            join(Trainers, Schedule.trainerid == Trainers.trainerid).\
            outerjoin(Locations, Schedule.locationid == Locations.locationid).\
            filter(Schedule.clientid == client_id).\
            order_by(Schedule.trainingdate, Schedule.trainingtime).all()

        result = []
        for schedule, trainer, location in schedules:
            row_dict = {
                'ID': schedule.scheduleid,
                'Дата': schedule.trainingdate.isoformat() if schedule.trainingdate else '—',
                'Время': schedule.trainingtime.isoformat() if schedule.trainingtime else '—',
                'Тренер': f"{trainer.firstname} {trainer.lastname}",
                'Локация': location.locationname if location else '—'
            }
            result.append(row_dict)
        return jsonify(result)
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        return jsonify({'error': f'Не удалось получить данные: {str(e)}'}), 500

# Маршрут для добавления задания
@app.route('/add_assignment', methods=['POST'])
def add_assignment():
    data = request.json
    trainer_id = data.get('trainer_id')
    client_id = data.get('client_id')
    task_text = data.get('task_text')
    due_date = data.get('due_date')

    if not trainer_id or not client_id or not task_text or not due_date:
        return jsonify({'error': 'Заполните все поля корректно!'}), 400

    try:
        new_assignment = Assignments(
            trainerid=trainer_id,
            clientid=client_id,
            tasktext=task_text,
            duedate=due_date
        )
        db.session.add(new_assignment)
        db.session.commit()
        return jsonify({'message': 'Задание добавлено!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Не удалось добавить задание: {str(e)}'}), 500

# Маршрут для получения заданий клиента
@app.route('/show_assignments', methods=['POST'])
def show_assignments():
    data = request.json
    client_id = data.get('client_id')

    if not client_id:
        return jsonify({'error': 'Введите ID клиента!'}), 400

    try:
        assignments = Assignments.query.filter_by(clientid=client_id).order_by(Assignments.duedate).all()
        result = [
            {
                'ID': a.assignmentid,
                'Задание': a.tasktext,
                'Дата': a.duedate.isoformat() if a.duedate else '—',
                'Статус': '✅ Выполнено' if a.iscompleted else '❌ Не выполнено'
            }
            for a in assignments
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Не удалось получить данные: {str(e)}'}), 500

# Маршрут для отметки задания как выполненного
@app.route('/mark_as_completed', methods=['POST'])
def mark_as_completed():
    data = request.json
    assignment_id = data.get('assignment_id')

    if not assignment_id:
        return jsonify({'error': 'Выберите задание!'}), 400

    try:
        assignment = Assignments.query.get(assignment_id)
        if not assignment or assignment.iscompleted:
            return jsonify({"error": "Не удалось отметить задание как выполненное"}), 400

        assignment.iscompleted = True
        db.session.commit()
        return jsonify({"message": "Задание отмечено как выполненное!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Не удалось обновить задание: {str(e)}'}), 500

# Маршрут для получения прогресса клиентов
@app.route('/show_progress', methods=['POST'])
def show_progress():
    data = request.json
    trainer_id = data.get('trainer_id')

    if not trainer_id:
        return jsonify({'error': 'Введите ID тренера!'}), 400

    try:
        assignments = db.session.query(Assignments, Clients).\
            join(Clients, Assignments.clientid == Clients.clientid).\
            filter(Assignments.trainerid == trainer_id).\
            order_by(Assignments.duedate).all()

        result = [
            {
                'Клиент': f"{client.firstname} {client.lastname}",
                'Задание': assignment.tasktext,
                'Дата': assignment.duedate.isoformat() if assignment.duedate else '—',
                'Статус': '✅ Выполнено' if assignment.iscompleted else '❌ Не выполнено'
            }
            for assignment, client in assignments
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Не удалось получить данные: {str(e)}'}), 500

# Проверка бейджа "3 недели без пропусков"
def check_no_absences_badge(client_id):
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=21)

        trainings = Schedule.query.filter(
            Schedule.clientid == client_id,
            Schedule.trainingdate.between(start_date, end_date),
            Schedule.status == 'Занято'
        ).order_by(Schedule.trainingdate).all()

        if not trainings:
            return False

        training_dates = [t.trainingdate for t in trainings]
        consecutive_days = 1
        for i in range(1, len(training_dates)):
            if (training_dates[i] - training_dates[i-1]).days == 1:
                consecutive_days += 1
            else:
                consecutive_days = 1
            if consecutive_days >= 21:
                break

        if consecutive_days >= 21:
            existing_badge = Achievements.query.filter_by(
                clientid=client_id,
                achievementname="3 недели без пропусков"
            ).first()
            if not existing_badge:
                new_badge = Achievements(
                    clientid=client_id,
                    achievementname="3 недели без пропусков",
                    dateearned=date.today()
                )
                db.session.add(new_badge)
                db.session.commit()
                return True
        return False
    except Exception as e:
        print(f"Ошибка при проверке бейджа '3 недели без пропусков': {e}")
        return False

# Проверка бейджа "10 выполненных заданий"
def check_completed_tasks_badge(client_id):
    try:
        completed_tasks = Assignments.query.filter_by(clientid=client_id, iscompleted=True).count()
        if completed_tasks >= 10:
            existing_badge = Achievements.query.filter_by(
                clientid=client_id,
                achievementname="10 выполненных заданий"
            ).first()
            if not existing_badge:
                new_badge = Achievements(
                    clientid=client_id,
                    achievementname="10 выполненных заданий",
                    dateearned=date.today()
                )
                db.session.add(new_badge)
                db.session.commit()
                return True
        return False
    except Exception as e:
        print(f"Ошибка при проверке бейджа '10 выполненных заданий': {e}")
        return False

# Маршрут для записи на тренировку
@app.route('/sign_up_for_training', methods=['POST'])
def sign_up_for_training():
    data = request.get_json()
    schedule_id = data.get('schedule_id')
    client_id = data.get('client_id')
    current_status = data.get('status')

    if not schedule_id or not client_id or not current_status:
        return jsonify({"error": "Отсутствуют необходимые данные"}), 400

    if current_status != "Свободно":
        return jsonify({"error": "Эта тренировка уже занята"}), 400

    try:
        schedule = Schedule.query.get(schedule_id)
        if not schedule or schedule.status != 'Свободно':
            return jsonify({"error": "Не удалось записаться на тренировку"}), 400

        schedule.clientid = client_id
        schedule.status = 'Занято'
        db.session.commit()
        return jsonify({"message": "Запись на тренировку успешна!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Маршрут для получения достижений клиента
@app.route('/client_achievements', methods=['POST'])
def client_achievements():
    data = request.get_json()
    client_id = data.get('client_id')

    try:
        achievements = Achievements.query.filter_by(clientid=client_id).all()
        result = [
            {
                "AchievementName": a.achievementname,
                "DateEarned": a.dateearned.strftime('%Y-%m-%d') if a.dateearned else '—'
            }
            for a in achievements
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Маршрут для получения расписания тренера
@app.route('/trainer_schedule', methods=['POST'])
def trainer_schedule():
    data = request.json
    trainer_id = data.get('trainer_id')

    if not trainer_id:
        return jsonify({'error': 'Выберите тренера!'}), 400

    try:
        schedules = db.session.query(Schedule, Locations).\
            outerjoin(Locations, Schedule.locationid == Locations.locationid).\
            filter(Schedule.trainerid == trainer_id).\
            order_by(Schedule.trainingdate, Schedule.trainingtime).all()

        result = []
        for schedule, location in schedules:
            row_dict = {
                'ID': schedule.scheduleid,
                'Дата': schedule.trainingdate.isoformat() if schedule.trainingdate else '—',
                'Время': schedule.trainingtime.isoformat() if schedule.trainingtime else '—',
                'Статус': schedule.status,
                'Локация': location.locationname if location else '—'
            }
            result.append(row_dict)
        return jsonify(result)
    except Exception as e:
        print(f"Ошибка в trainer_schedule: {str(e)}")
        return jsonify({'error': f'Ошибка при получении расписания: {str(e)}'}), 500

# Маршрут для получения профиля клиента
@app.route('/client_profile/<int:client_id>', methods=['GET'])
def get_client_profile(client_id):
    try:
        client = Clients.query.get(client_id)
        if client:
            return jsonify({
                'firstname': client.firstname,
                'lastname': client.lastname,
                'phonenumber': client.phonenumber,
                'dob': client.dob.isoformat() if client.dob else None,
                'medicalrecords': client.medicalrecords
            })
        return jsonify({'error': 'Клиент не найден'}), 404
    except Exception as e:
        return jsonify({'error': f'Не удалось получить данные: {str(e)}'}), 500

# Маршрут для получения профиля тренера
@app.route('/trainer_profile/<int:trainer_id>', methods=['GET'])
def get_trainer_profile(trainer_id):
    try:
        trainer = Trainers.query.get(trainer_id)
        if trainer:
            return jsonify({
                'firstname': trainer.firstname,
                'lastname': trainer.lastname,
                'specialty': trainer.specialty,
                'phonenumber': trainer.phonenumber,
                'dob': trainer.dob.isoformat() if trainer.dob else None,
                'experience': trainer.experience
            })
        return jsonify({'error': 'Тренер не найден'}), 404
    except Exception as e:
        return jsonify({'error': f'Не удалось получить данные: {str(e)}'}), 500

# Маршрут для обновления профиля тренера
# Маршрут для обновления профиля тренера
@app.route('/trainer_profile/<int:trainer_id>', methods=['PUT'])
def update_trainer_profile(trainer_id):
    try:
        trainer = Trainers.query.get(trainer_id)
        if trainer:
            data = request.get_json()
            trainer.firstname = data.get('firstname', trainer.firstname)
            trainer.lastname = data.get('lastname', trainer.lastname)
            trainer.specialty = data.get('specialty', trainer.specialty)
            trainer.phonenumber = data.get('phonenumber', trainer.phonenumber)
            trainer.dob = data.get('dob', trainer.dob)
            trainer.experience = data.get('experience', trainer.experience)

            db.session.commit()
            return jsonify({'message': 'Профиль обновлен'})
        return jsonify({'error': 'Тренер не найден'}), 404
    except Exception as e:
        return jsonify({'error': f'Не удалось обновить данные: {str(e)}'}), 500

# Маршрут для обновления профиля клиента
@app.route('/client_profile/<int:client_id>', methods=['PUT'])
def update_client_profile(client_id):
    try:
        client = Clients.query.get(client_id)
        if client:
            data = request.get_json()
            client.firstname = data.get('firstname', client.firstname)
            client.lastname = data.get('lastname', client.lastname)
            client.phonenumber = data.get('phonenumber', client.phonenumber)
            client.dob = data.get('dob', client.dob)
            client.medicalrecords = data.get('medicalrecords', client.medicalrecords)

            db.session.commit()
            return jsonify({'message': 'Профиль обновлен'})
        return jsonify({'error': 'Клиент не найден'}), 404
    except Exception as e:
        return jsonify({'error': f'Не удалось обновить данные: {str(e)}'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создает таблицы, если они еще не существуют
    app.run(debug=True, host='127.0.0.1', port=5000)