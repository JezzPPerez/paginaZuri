import os
from datetime import datetime, timedelta
from app import app, db, Transaction, RecurringService, WeeklyGoal

def seed_data():
    with app.app_context():
        # Limpiar datos existentes si los hay
        db.drop_all()
        db.create_all()

        print("Base de datos limpia e inicializada.")

        # Fechas dinámicas relativas a hoy
        today = datetime.now()
        
        # Calcular el lunes de esta semana
        monday = today - timedelta(days=today.weekday())
        monday_str = monday.strftime('%Y-%m-%d')
        
        # Crear la meta semanal actual
        goal = WeeklyGoal(
            week_start_date=monday_str,
            target_income=12000.00,
            target_savings=3000.00
        )
        db.session.add(goal)

        # Transacciones de ejemplo
        transactions = [
            # Ingresos de esta semana
            Transaction(
                date=(monday + timedelta(days=0)).strftime('%Y-%m-%d'), # Lunes
                description="Pago de Nómina (Semanal)",
                amount=9500.00,
                type="income",
                category="Trabajo / Inversión",
                payment_method="Débito"
            ),
            Transaction(
                date=(monday + timedelta(days=2)).strftime('%Y-%m-%d'), # Miércoles
                description="Proyecto Freelance (Diseño Web)",
                amount=3500.00,
                type="income",
                category="Trabajo / Inversión",
                payment_method="Débito"
            ),
            
            # Gastos de esta semana
            Transaction(
                date=(monday + timedelta(days=0)).strftime('%Y-%m-%d'),
                description="Suscripción Netflix",
                amount=249.00,
                type="expense",
                category="Suscripción",
                payment_method="Crédito"
            ),
            Transaction(
                date=(monday + timedelta(days=1)).strftime('%Y-%m-%d'),
                description="Café Starbucks y Dona",
                amount=125.00,
                type="expense",
                category="Gasto Hormiga",
                payment_method="Débito"
            ),
            Transaction(
                date=(monday + timedelta(days=2)).strftime('%Y-%m-%d'),
                description="Pago de Internet Telmex",
                amount=499.00,
                type="expense",
                category="Servicio",
                payment_method="Débito"
            ),
            Transaction(
                date=(monday + timedelta(days=3)).strftime('%Y-%m-%d'),
                description="Inversión en Campaña Facebook Ads (Trabajo)",
                amount=1800.00,
                type="expense",
                category="Trabajo / Inversión",
                payment_method="Crédito"
            ),
            Transaction(
                date=(monday + timedelta(days=4)).strftime('%Y-%m-%d'), # Viernes
                description="Cena en Restaurante (Fin de Semana)",
                amount=850.00,
                type="expense",
                category="Fin de Semana",
                payment_method="Crédito"
            ),
            Transaction(
                date=(monday + timedelta(days=4)).strftime('%Y-%m-%d'), # Viernes
                description="Taxis / Uber de regreso",
                amount=180.00,
                type="expense",
                category="Fin de Semana",
                payment_method="Débito"
            ),
            
            # Historial de semanas anteriores para tener histórico en Dashboard
            Transaction(
                date=(monday - timedelta(days=4)).strftime('%Y-%m-%d'), # Jueves de semana pasada
                description="Supermercado Semanal",
                amount=1200.00,
                type="expense",
                category="Otros",
                payment_method="Débito"
            ),
            Transaction(
                date=(monday - timedelta(days=3)).strftime('%Y-%m-%d'), # Viernes de semana pasada
                description="Salida a Bar / Cervezas",
                amount=950.00,
                type="expense",
                category="Fin de Semana",
                payment_method="Crédito"
            ),
            Transaction(
                date=(monday - timedelta(days=2)).strftime('%Y-%m-%d'), # Sábado de semana pasada
                description="Entradas de Cine e combos",
                amount=450.00,
                type="expense",
                category="Fin de Semana",
                payment_method="Crédito"
            ),
            Transaction(
                date=(monday - timedelta(days=1)).strftime('%Y-%m-%d'), # Domingo de semana pasada
                description="Ahorro Automático programado",
                amount=2000.00,
                type="expense",
                category="Ahorro",
                payment_method="Débito"
            ),
        ]

        for tx in transactions:
            db.session.add(tx)

        # Servicios Recurrentes Programados
        recurring_services = [
            RecurringService(
                name="Netflix Premium",
                amount=249.00,
                frequency="Mensual",
                next_billing_date=(today + timedelta(days=5)).strftime('%Y-%m-%d'),
                category="Suscripción",
                payment_method="Crédito"
            ),
            RecurringService(
                name="Spotify Familiar",
                amount=199.00,
                frequency="Mensual",
                next_billing_date=(today + timedelta(days=12)).strftime('%Y-%m-%d'),
                category="Suscripción",
                payment_method="Crédito"
            ),
            RecurringService(
                name="Servicio de Luz CFE",
                amount=540.00,
                frequency="Mensual",
                next_billing_date=(today + timedelta(days=8)).strftime('%Y-%m-%d'),
                category="Servicio",
                payment_method="Débito"
            ),
            RecurringService(
                name="Hosting Web Dominio",
                amount=89.00,
                frequency="Mensual",
                next_billing_date=(today + timedelta(days=15)).strftime('%Y-%m-%d'),
                category="Trabajo / Inversión",
                payment_method="Débito"
            ),
            RecurringService(
                name="Seguro de Auto",
                amount=9600.00,
                frequency="Anual",
                next_billing_date=(today + timedelta(days=45)).strftime('%Y-%m-%d'),
                category="Otros",
                payment_method="Crédito"
            )
        ]

        for rs in recurring_services:
            db.session.add(rs)

        db.session.commit()
        print("¡Base de datos sembrada con datos de prueba exitosamente!")

if __name__ == '__main__':
    seed_data()
