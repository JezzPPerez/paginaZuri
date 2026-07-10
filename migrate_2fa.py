import os
import sqlite3

def run_2fa_migration():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'finance.db')
    
    if not os.path.exists(db_path):
        print("La base de datos no existe todavía. Al iniciar la aplicación se creará con el nuevo esquema automáticamente.")
        return

    print("Iniciando migración para agregar 2FA...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Intentamos agregar la columna otp_secret a la tabla users
        cursor.execute("ALTER TABLE users ADD COLUMN otp_secret VARCHAR(32)")
        conn.commit()
        print("Columna 'otp_secret' agregada con éxito a la tabla 'users'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
            print("La columna 'otp_secret' ya existe. No se requiere realizar ningún cambio.")
        else:
            print("Ocurrió un error al alterar la tabla:", e)
    finally:
        conn.close()
        print("Migración finalizada.")

if __name__ == '__main__':
    run_2fa_migration()
