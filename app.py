import os
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp

app = Flask(__name__)

# Configuración de Clave Secreta para Sesiones
app.secret_key = 'finanzaspro_secret_key_super_secure_123'

# Configuración de la Base de Datos (PostgreSQL en producción, SQLite local)
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Render/Heroku envían "postgres://", pero SQLAlchemy 2.0 requiere "postgresql://"
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'finance.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Modelos de Base de Datos ---

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    otp_secret = db.Column(db.String(32), nullable=True)  # Secreto para 2FA (Base32)

    # Relaciones
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade="all, delete-orphan")
    recurring_services = db.relationship('RecurringService', backref='user', lazy=True, cascade="all, delete-orphan")
    weekly_goals = db.relationship('WeeklyGoal', backref='user', lazy=True, cascade="all, delete-orphan")
    debts = db.relationship('Debt', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' o 'expense'
    category = db.Column(db.String(50), nullable=False) # 'Trabajo / Inversión', 'Gasto Hormiga', 'Suscripción', 'Servicio', 'Fin de Semana', 'Ahorro', 'Otros'
    payment_method = db.Column(db.String(20), nullable=False)  # 'Débito', 'Crédito', 'Efectivo'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date,
            'description': self.description,
            'amount': self.amount,
            'type': self.type,
            'category': self.category,
            'payment_method': self.payment_method
        }


class RecurringService(db.Model):
    __tablename__ = 'recurring_services'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # 'Semanal', 'Mensual', 'Anual'
    next_billing_date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    category = db.Column(db.String(50), nullable=False)  # 'Suscripción', 'Servicio', 'Otros'
    payment_method = db.Column(db.String(20), nullable=False)  # 'Débito', 'Crédito'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'amount': self.amount,
            'frequency': self.frequency,
            'next_billing_date': self.next_billing_date,
            'category': self.category,
            'payment_method': self.payment_method
        }


class WeeklyGoal(db.Model):
    __tablename__ = 'weekly_goals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    week_start_date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    target_income = db.Column(db.Float, default=0.0)
    target_savings = db.Column(db.Float, default=0.0)

    __table_args__ = (db.UniqueConstraint('user_id', 'week_start_date', name='_user_week_uc'),)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'week_start_date': self.week_start_date,
            'target_income': self.target_income,
            'target_savings': self.target_savings
        }


class Debt(db.Model):
    __tablename__ = 'debts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    person_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'lend' (me deben) o 'borrow' (debo)
    description = db.Column(db.String(200), nullable=True)
    due_date = db.Column(db.String(10), nullable=True)  # YYYY-MM-DD
    status = db.Column(db.String(20), default='pending')  # 'pending' o 'paid'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'person_name': self.person_name,
            'amount': self.amount,
            'type': self.type,
            'description': self.description,
            'due_date': self.due_date,
            'status': self.status
        }


# --- Decorador de Autenticación ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'No autorizado'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# --- Rutas de Autenticación e Interfaz ---

@app.route('/')
@login_required
def index():
    return render_template('index.html', username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['temp_user_id'] = user.id
            return redirect(url_for('login_2fa'))
        else:
            error = 'Usuario o contraseña incorrectos.'
            
    return render_template('login.html', error=error)

@app.route('/login-2fa', methods=['GET', 'POST'])
def login_2fa():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    temp_user_id = session.get('temp_user_id')
    if not temp_user_id:
        return redirect(url_for('login'))
        
    user = User.query.get(temp_user_id)
    if not user:
        session.clear()
        return redirect(url_for('login'))
        
    is_setup = user.otp_secret is None
    
    if is_setup:
        # Generar un secreto temporal de 2FA y mantenerlo en sesión hasta confirmar
        if 'temp_otp_secret' not in session:
            session['temp_otp_secret'] = pyotp.random_base32()
        otp_secret = session['temp_otp_secret']
        provisioning_uri = pyotp.totp.TOTP(otp_secret).provisioning_uri(
            name=user.username,
            issuer_name="Finanzas JZ"
        )
    else:
        otp_secret = user.otp_secret
        provisioning_uri = None

    error = None
    if request.method == 'POST':
        token = request.form.get('otp_token')
        if token and len(token) == 6 and token.isdigit():
            totp = pyotp.TOTP(otp_secret)
            # valid_window=1 otorga 30s de tolerancia antes y después
            if totp.verify(token, valid_window=1):
                if is_setup:
                    user.otp_secret = otp_secret
                    db.session.commit()
                    session.pop('temp_otp_secret', None)
                
                # Completar el inicio de sesión
                session['user_id'] = user.id
                session['username'] = user.username
                session.pop('temp_user_id', None)
                return redirect(url_for('index'))
            else:
                error = 'Código de seguridad incorrecto o expirado.'
        else:
            error = 'Por favor introduce un código de 6 dígitos válido.'

    return render_template(
        'login_2fa.html', 
        is_setup=is_setup, 
        otp_secret=otp_secret, 
        provisioning_uri=provisioning_uri,
        error=error
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- Rutas de la API ---

# 1. Transacciones
@app.route('/api/transactions', methods=['GET'])
@login_required
def get_transactions():
    t_type = request.args.get('type')
    category = request.args.get('category')
    
    query = Transaction.query.filter_by(user_id=session['user_id'])
    if t_type:
        query = query.filter_by(type=t_type)
    if category:
        query = query.filter_by(category=category)
        
    transactions = query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()
    return jsonify([t.to_dict() for t in transactions])

@app.route('/api/transactions', methods=['POST'])
@login_required
def create_transaction():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        new_transaction = Transaction(
            user_id=session['user_id'],
            date=data['date'],
            description=data['description'],
            amount=float(data['amount']),
            type=data['type'],
            category=data['category'],
            payment_method=data['payment_method']
        )
        db.session.add(new_transaction)
        db.session.commit()
        return jsonify(new_transaction.to_dict()), 201
    except KeyError as e:
        return jsonify({'error': f'Falta el campo requerido: {str(e)}'}), 400
    except ValueError:
        return jsonify({'error': 'Monto inválido'}), 400

@app.route('/api/transactions/<int:id>', methods=['PUT'])
@login_required
def update_transaction(id):
    transaction = Transaction.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        transaction.date = data.get('date', transaction.date)
        transaction.description = data.get('description', transaction.description)
        transaction.amount = float(data.get('amount', transaction.amount))
        transaction.type = data.get('type', transaction.type)
        transaction.category = data.get('category', transaction.category)
        transaction.payment_method = data.get('payment_method', transaction.payment_method)
        
        db.session.commit()
        return jsonify(transaction.to_dict())
    except ValueError:
        return jsonify({'error': 'Monto inválido'}), 400

@app.route('/api/transactions/<int:id>', methods=['DELETE'])
@login_required
def delete_transaction(id):
    transaction = Transaction.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    db.session.delete(transaction)
    db.session.commit()
    return jsonify({'message': 'Transacción eliminada con éxito'})


# 2. Servicios Recurrentes
@app.route('/api/recurring', methods=['GET'])
@login_required
def get_recurring():
    services = RecurringService.query.filter_by(user_id=session['user_id']).order_by(RecurringService.next_billing_date.asc()).all()
    return jsonify([s.to_dict() for s in services])

@app.route('/api/recurring', methods=['POST'])
@login_required
def create_recurring():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        new_service = RecurringService(
            user_id=session['user_id'],
            name=data['name'],
            amount=float(data['amount']),
            frequency=data['frequency'],
            next_billing_date=data['next_billing_date'],
            category=data['category'],
            payment_method=data['payment_method']
        )
        db.session.add(new_service)
        db.session.commit()
        return jsonify(new_service.to_dict()), 201
    except KeyError as e:
        return jsonify({'error': f'Falta el campo requerido: {str(e)}'}), 400

@app.route('/api/recurring/<int:id>', methods=['PUT'])
@login_required
def update_recurring(id):
    service = RecurringService.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        service.name = data.get('name', service.name)
        service.amount = float(data.get('amount', service.amount))
        service.frequency = data.get('frequency', service.frequency)
        service.next_billing_date = data.get('next_billing_date', service.next_billing_date)
        service.category = data.get('category', service.category)
        service.payment_method = data.get('payment_method', service.payment_method)
        
        db.session.commit()
        return jsonify(service.to_dict())
    except ValueError:
        return jsonify({'error': 'Monto inválido'}), 400

@app.route('/api/recurring/<int:id>', methods=['DELETE'])
@login_required
def delete_recurring(id):
    service = RecurringService.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    db.session.delete(service)
    db.session.commit()
    return jsonify({'message': 'Servicio recurrente eliminado con éxito'})


# 3. Metas Semanales
@app.route('/api/goals', methods=['GET'])
@login_required
def get_goals():
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    monday_str = monday.strftime('%Y-%m-%d')
    
    goal = WeeklyGoal.query.filter_by(user_id=session['user_id'], week_start_date=monday_str).first()
    if not goal:
        return jsonify({
            'week_start_date': monday_str,
            'target_income': 0.0,
            'target_savings': 0.0,
            'is_new': True
        })
    
    res = goal.to_dict()
    res['is_new'] = False
    return jsonify(res)

@app.route('/api/goals', methods=['POST'])
@login_required
def save_goal():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        monday_str = data['week_start_date']
        target_income = float(data.get('target_income', 0.0))
        target_savings = float(data.get('target_savings', 0.0))
        
        goal = WeeklyGoal.query.filter_by(user_id=session['user_id'], week_start_date=monday_str).first()
        if goal:
            goal.target_income = target_income
            goal.target_savings = target_savings
        else:
            goal = WeeklyGoal(
                user_id=session['user_id'],
                week_start_date=monday_str,
                target_income=target_income,
                target_savings=target_savings
            )
            db.session.add(goal)
            
        db.session.commit()
        return jsonify(goal.to_dict())
    except KeyError as e:
        return jsonify({'error': f'Falta el campo requerido: {str(e)}'}), 400


# 4. Deudas y Préstamos
@app.route('/api/debts', methods=['GET'])
@login_required
def get_debts():
    debts = Debt.query.filter_by(user_id=session['user_id']).order_by(Debt.status.desc(), Debt.due_date.asc()).all()
    return jsonify([d.to_dict() for d in debts])

@app.route('/api/debts', methods=['POST'])
@login_required
def create_debt():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        new_debt = Debt(
            user_id=session['user_id'],
            person_name=data['person_name'],
            amount=float(data['amount']),
            type=data['type'],
            description=data.get('description', ''),
            due_date=data.get('due_date', ''),
            status=data.get('status', 'pending')
        )
        db.session.add(new_debt)
        db.session.commit()
        return jsonify(new_debt.to_dict()), 201
    except KeyError as e:
        return jsonify({'error': f'Falta el campo requerido: {str(e)}'}), 400
    except ValueError:
        return jsonify({'error': 'Monto inválido'}), 400

@app.route('/api/debts/<int:id>', methods=['PUT'])
@login_required
def update_debt(id):
    debt = Debt.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        debt.person_name = data.get('person_name', debt.person_name)
        debt.amount = float(data.get('amount', debt.amount))
        debt.type = data.get('type', debt.type)
        debt.description = data.get('description', debt.description)
        debt.due_date = data.get('due_date', debt.due_date)
        debt.status = data.get('status', debt.status)
        
        db.session.commit()
        return jsonify(debt.to_dict())
    except ValueError:
        return jsonify({'error': 'Monto inválido'}), 400

@app.route('/api/debts/<int:id>', methods=['DELETE'])
@login_required
def delete_debt(id):
    debt = Debt.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    db.session.delete(debt)
    db.session.commit()
    return jsonify({'message': 'Deuda eliminada con éxito'})


# 5. Resumen Estadístico para el Dashboard
@app.route('/api/summary', methods=['GET'])
@login_required
def get_summary():
    u_id = session['user_id']
    transactions = Transaction.query.filter_by(user_id=u_id).all()
    
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')
    net_balance = total_income - total_expense
    
    debit_expenses = sum(t.amount for t in transactions if t.type == 'expense' and t.payment_method == 'Débito')
    credit_expenses = sum(t.amount for t in transactions if t.type == 'expense' and t.payment_method == 'Crédito')
    
    categories_breakdown = {}
    for t in transactions:
        if t.type == 'expense':
            categories_breakdown[t.category] = categories_breakdown.get(t.category, 0.0) + t.amount
            
    weekend_expenses = 0.0
    for t in transactions:
        if t.type == 'expense':
            try:
                date_obj = datetime.strptime(t.date, '%Y-%m-%d')
                if date_obj.weekday() in [5, 6]:
                    weekend_expenses += t.amount
            except ValueError:
                pass
                
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    
    monday_str = monday.strftime('%Y-%m-%d')
    sunday_str = sunday.strftime('%Y-%m-%d')
    
    weekly_transactions = Transaction.query.filter(
        Transaction.user_id == u_id,
        Transaction.date >= monday_str,
        Transaction.date <= sunday_str
    ).all()
    
    weekly_income = sum(t.amount for t in weekly_transactions if t.type == 'income')
    weekly_expenses = sum(t.amount for t in weekly_transactions if t.type == 'expense')
    weekly_savings = weekly_income - weekly_expenses
    
    goal = WeeklyGoal.query.filter_by(user_id=u_id, week_start_date=monday_str).first()
    target_income = goal.target_income if goal else 0.0
    target_savings = goal.target_savings if goal else 0.0
    
    # Cálculos de Deudas
    debts = Debt.query.filter_by(user_id=u_id, status='pending').all()
    total_owed_to_me = sum(d.amount for d in debts if d.type == 'lend')
    total_i_owe = sum(d.amount for d in debts if d.type == 'borrow')
    
    # Alertas de Pagos Recurrentes (Próximos 10 días)
    services = RecurringService.query.filter_by(user_id=u_id).all()
    upcoming_alerts = []
    today_date = datetime.now().date()
    
    for s in services:
        try:
            billing_date = datetime.strptime(s.next_billing_date, '%Y-%m-%d').date()
            days_left = (billing_date - today_date).days
            # Considerar cobros de hoy hasta dentro de 10 días
            if 0 <= days_left <= 10:
                upcoming_alerts.append({
                    'name': s.name,
                    'amount': s.amount,
                    'next_billing_date': s.next_billing_date,
                    'category': s.category,
                    'days_left': days_left
                })
        except ValueError:
            pass
            
    upcoming_alerts.sort(key=lambda x: x['days_left'])
    
    return jsonify({
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': net_balance,
        'debit_expenses': debit_expenses,
        'credit_expenses': credit_expenses,
        'categories_breakdown': categories_breakdown,
        'weekend_expenses': weekend_expenses,
        'total_owed_to_me': total_owed_to_me,
        'total_i_owe': total_i_owe,
        'upcoming_alerts': upcoming_alerts,
        'weekly_progress': {
            'week_start': monday_str,
            'week_end': sunday_str,
            'actual_income': weekly_income,
            'target_income': target_income,
            'actual_savings': weekly_savings,
            'target_savings': target_savings
        }
    })

# Inicializar Base de Datos
with app.app_context():
    db.create_all()
    try:
        if User.query.count() == 0:
            user_jezzito = User(username='jezzito')
            user_jezzito.set_password('jezzito123')
            
            user_rabanito = User(username='Rabanito')
            user_rabanito.set_password('rabanito123')
            
            db.session.add(user_jezzito)
            db.session.add(user_rabanito)
            db.session.commit()
            print("Usuarios por defecto creados en la base de datos.")
    except Exception as e:
        print("Error al inicializar usuarios por defecto:", e)

if __name__ == '__main__':
    # Escuchar en 0.0.0.0 para acceso en red local (celular)
    app.run(debug=True, host='0.0.0.0', port=5000)
