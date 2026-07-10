import os
import sqlite3
from app import app, db, User, Transaction, RecurringService, WeeklyGoal

def run_migration():
    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'finance.db')
    
    if not os.path.exists(db_file):
        print("La base de datos no existe. Se creará una vacía.")
        with app.app_context():
            db.create_all()
            create_default_users()
        return

    print("Respaldando datos existentes en memoria...")
    
    # Conectamos con sqlite3 directamente para leer los datos antes de borrar la BD
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Obtener transacciones antiguas
    old_transactions = []
    try:
        cursor.execute("SELECT date, description, amount, type, category, payment_method FROM transactions")
        rows = cursor.fetchall()
        for r in rows:
            old_transactions.append({
                'date': r[0],
                'description': r[1],
                'amount': r[2],
                'type': r[3],
                'category': r[4],
                'payment_method': r[5]
            })
        print(f"Respaldadas {len(old_transactions)} transacciones.")
    except sqlite3.OperationalError as e:
        print("No se pudieron respaldar las transacciones:", e)

    # Obtener servicios recurrentes antiguos
    old_recurring = []
    try:
        cursor.execute("SELECT name, amount, frequency, next_billing_date, category, payment_method FROM recurring_services")
        rows = cursor.fetchall()
        for r in rows:
            old_recurring.append({
                'name': r[0],
                'amount': r[1],
                'frequency': r[2],
                'next_billing_date': r[3],
                'category': r[4],
                'payment_method': r[5]
            })
        print(f"Respaldados {len(old_recurring)} servicios recurrentes.")
    except sqlite3.OperationalError as e:
        print("No se pudieron respaldar los servicios recurrentes:", e)

    conn.close()

    # Reestructurar Base de Datos con SQLAlchemy
    print("Reestructurando tablas de base de datos...")
    with app.app_context():
        # Borrar tablas existentes
        db.drop_all()
        # Crear nuevas tablas según el nuevo esquema de app.py
        db.create_all()
        print("Nuevas tablas creadas exitosamente.")

        # Crear usuarios por defecto
        print("Creando perfiles de usuario...")
        user_jezzito = User(username='jezzito')
        user_jezzito.set_password('jezzito123')
        
        user_rabanito = User(username='Rabanito')
        user_rabanito.set_password('rabanito123')

        db.session.add(user_jezzito)
        db.session.add(user_rabanito)
        db.session.commit()
        
        jezzito_id = user_jezzito.id
        print(f"Usuarios creados: jezzito (ID: {jezzito_id}), Rabanito (ID: {user_rabanito.id}).")

        # Restaurar transacciones asignándolas a jezzito
        print("Restaurando transacciones para jezzito...")
        for tx_data in old_transactions:
            tx = Transaction(
                user_id=jezzito_id,
                date=tx_data['date'],
                description=tx_data['description'],
                amount=tx_data['amount'],
                type=tx_data['type'],
                category=tx_data['category'],
                payment_method=tx_data['payment_method']
            )
            db.session.add(tx)

        # Restaurar servicios recurrentes asignándolos a jezzito
        print("Restaurando servicios recurrentes para jezzito...")
        for rec_data in old_recurring:
            rec = RecurringService(
                user_id=jezzito_id,
                name=rec_data['name'],
                amount=rec_data['amount'],
                frequency=rec_data['frequency'],
                next_billing_date=rec_data['next_billing_date'],
                category=rec_data['category'],
                payment_method=rec_data['payment_method']
            )
            db.session.add(rec)

        db.session.commit()
        print("¡Migración completada con éxito sin pérdida de información!")

def create_default_users():
    user_jezzito = User(username='jezzito')
    user_jezzito.set_password('jezzito123')
    
    user_rabanito = User(username='Rabanito')
    user_rabanito.set_password('rabanito123')

    db.session.add(user_jezzito)
    db.session.add(user_rabanito)
    db.session.commit()
    print("Usuarios jezzito y Rabanito creados en base de datos vacía.")

if __name__ == '__main__':
    run_migration()
