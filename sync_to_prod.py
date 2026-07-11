import os
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from app import db, User, Transaction, RecurringService, WeeklyGoal

def sync():
    print("=== Sincronizador de Datos Local a Produccion ===")
    
    # Pedir el URL de base de datos de producción
    prod_url = input("Ingresa tu DATABASE_URL de Render (ej. postgresql://...): ").strip()
    if not prod_url:
        print("URL no valida. Cancelando.")
        return
        
    if prod_url.startswith("postgres://"):
        prod_url = prod_url.replace("postgres://", "postgresql://", 1)
        
    local_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'finance.db')
    if not os.path.exists(local_db):
        print("No se encontro base de datos local 'finance.db' para migrar.")
        return

    print("Leyendo datos locales...")
    local_engine = sqlalchemy.create_engine(f'sqlite:///{local_db}')
    LocalSession = sessionmaker(bind=local_engine)
    local_session = LocalSession()
    
    try:
        local_users = local_session.query(User).all()
        local_txs = local_session.query(Transaction).all()
        local_services = local_session.query(RecurringService).all()
        local_goals = local_session.query(WeeklyGoal).all()
    except Exception as e:
        print("Error al leer datos locales. Asegurate de que no este corrupta la BD:", e)
        local_session.close()
        return
    
    print(f"Encontrados en local: {len(local_users)} usuarios, {len(local_txs)} transacciones, {len(local_services)} servicios, {len(local_goals)} metas.")
    
    print("\nConectando a base de datos de produccion (PostgreSQL)...")
    try:
        prod_engine = sqlalchemy.create_engine(prod_url)
        ProdSession = sessionmaker(bind=prod_engine)
        prod_session = ProdSession()
        
        confirm = input("¿Deseas sobreescribir la base de datos de produccion con tus datos locales? (s/n): ").lower()
        if confirm != 's':
            print("Cancelado por el usuario.")
            local_session.close()
            return
            
        print("Limpiando tablas en produccion...")
        prod_session.query(Transaction).delete()
        prod_session.query(RecurringService).delete()
        prod_session.query(WeeklyGoal).delete()
        prod_session.query(User).delete()
        prod_session.commit()
        
        print("Copiando usuarios...")
        user_mapping = {}
        for u in local_users:
            new_u = User(
                username=u.username,
                password_hash=u.password_hash,
                otp_secret=u.otp_secret
            )
            prod_session.add(new_u)
            prod_session.flush()
            user_mapping[u.id] = new_u.id
            
        print("Copiando transacciones...")
        for t in local_txs:
            new_t = Transaction(
                user_id=user_mapping.get(t.user_id),
                date=t.date,
                description=t.description,
                amount=t.amount,
                type=t.type,
                category=t.category,
                payment_method=t.payment_method
            )
            prod_session.add(new_t)
            
        print("Copiando servicios recurrentes...")
        for s in local_services:
            new_s = RecurringService(
                user_id=user_mapping.get(s.user_id),
                name=s.name,
                amount=s.amount,
                frequency=s.frequency,
                next_billing_date=s.next_billing_date,
                category=s.category,
                payment_method=s.payment_method
            )
            prod_session.add(new_s)
            
        print("Copiando metas semanales...")
        for g in local_goals:
            new_g = WeeklyGoal(
                user_id=user_mapping.get(g.user_id),
                week_start_date=g.week_start_date,
                target_income=g.target_income,
                target_savings=g.target_savings
            )
            prod_session.add(new_g)
            
        prod_session.commit()
        print("\n¡Sincronizacion finalizada con exito! Todos tus datos locales estan ahora en internet.")
        
    except Exception as e:
        print("\nOcurrio un error durante la sincronizacion:", e)
    finally:
        local_session.close()

if __name__ == '__main__':
    sync()
