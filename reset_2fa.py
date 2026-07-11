import sqlalchemy
from sqlalchemy.orm import sessionmaker
from app import User

def reset_2fa():
    print("=== Restablecedor de Seguridad 2FA (Produccion) ===")
    
    prod_url = input("Ingresa tu DATABASE_URL externa de Render (ej. postgresql://...): ").strip()
    if not prod_url:
        print("URL no valida. Cancelando.")
        return
        
    if prod_url.startswith("postgres://"):
        prod_url = prod_url.replace("postgres://", "postgresql://", 1)
        
    print("\nConectando a base de datos de produccion (PostgreSQL)...")
    try:
        engine = sqlalchemy.create_engine(prod_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Buscar usuarios
        users = session.query(User).all()
        if not users:
            print("No se encontraron usuarios en la base de datos.")
            session.close()
            return
            
        print("\nUsuarios encontrados:")
        for idx, u in enumerate(users):
            status_2fa = "Activo" if u.otp_secret else "No configurado"
            print(f"{idx + 1}. {u.username} (2FA: {status_2fa})")
            
        confirm = input("\n¿Deseas restablecer el 2FA para TODOS los usuarios? (s/n): ").lower()
        if confirm == 's':
            for u in users:
                u.otp_secret = None
            session.commit()
            print("\n¡2FA restablecido con exito! Ahora todos los usuarios mostraran el codigo QR al iniciar sesion de nuevo.")
        else:
            username_target = input("Ingresa el nombre del usuario específico a restablecer (ej. jezzito): ").strip()
            target_user = session.query(User).filter_by(username=username_target).first()
            if target_user:
                target_user.otp_secret = None
                session.commit()
                print(f"\n¡2FA restablecido con exito para {username_target}!")
            else:
                print(f"Usuario {username_target} no encontrado.")
                
        session.close()
    except Exception as e:
        print("\nOcurrio un error al intentar restablecer el 2FA:", e)

if __name__ == '__main__':
    reset_2fa()
