from sqlmodel import SQLModel, create_engine, Session

# Формат: postgresql://пользователь:пароль@хост:порт/имя_базы
DATABASE_URL = "postgresql://postgres:puee2OSOJYZxFAaM@localhost/car_rental_db"

engine = create_engine(DATABASE_URL, echo=False)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    