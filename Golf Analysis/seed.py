from AnalysisApp.database import SessionLocal
from AnalysisApp.models import Users
from AnalysisApp.routers.auth import bcrypt_context

def create_admin():
    db = SessionLocal()

    try: 
        admin = db.query(Users).filter(Users.username == "admin").first()

        if admin is None:
            db.add(
                Users(
                    username="admin",
                    email="admin@email.com",
                    first_name="Reid",
                    last_name="Boyko",
                    hashed_password=bcrypt_context.hash("adminpassword"),
                    admin=True
                )
            )
            db.commit()
            print('Admin user created')

        else:
            print('Admin user already exists')

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()



if __name__ == '__main__':
    create_admin()