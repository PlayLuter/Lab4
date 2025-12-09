# requests.py
from sqlmodel import SQLModel, Session, select, func
from datetime import datetime, timedelta, date
from decimal import Decimal

# Импортируем наши файлы
from database import engine
from models import *

def create_db_and_tables():
    """Создает таблицы в БД PostgreSQL"""
    SQLModel.metadata.create_all(engine)
    print("Таблицы успешно созданы!")

def seed_data():
    """Наполняет БД начальными данными"""
    with Session(engine) as session:
        # Проверка, чтобы не дублировать данные
        if session.exec(select(CarModel)).first():
            print("Данные уже существуют, пропускаем наполнение.")
            return

        # 1. Создаем Модели
        camry = CarModel(brand="Toyota", model_name="Camry", car_class="Business", daily_rate=3500, deposit_amount=15000)
        rio = CarModel(brand="Kia", model_name="Rio", car_class="Economy", daily_rate=2000, deposit_amount=5000)
        session.add(camry)
        session.add(rio)
        session.commit() # Чтобы получить ID моделей

        # 2. Создаем Авто
        car1 = Vehicle(model_id=camry.id, license_plate="A001AA777", vin_code="VIN1234567890", color="Black", current_mileage=10000, status="Available")
        car2 = Vehicle(model_id=rio.id, license_plate="B002BB777", vin_code="VIN0987654321", color="White", current_mileage=55000, status="Rented")
        session.add(car1)
        session.add(car2)
        
        # 3. Создаем Клиента и Сотрудника
        client = Client(full_name="Иванов Иван Иванович", driver_license_num="9900 123456", passport_data="4510 123123", phone="+79001234567", birth_date=date(1990, 1, 1))
        manager = Employee(full_name="Петров Петр", position="Менеджер")
        session.add(client)
        session.add(manager)
        session.commit()

        # 4. Создаем Заказ (Активный, на Kia Rio)
        order = RentalOrder(
            client_id=client.id,
            vehicle_id=car2.id,
            employee_id=manager.id,
            start_date=datetime.now() - timedelta(days=2), # Взял 2 дня назад
            end_date_planned=datetime.now() + timedelta(days=1),
            total_cost=6000, # 3 дня * 2000
            payment_status="Partial"
        )
        session.add(order)
        session.commit()

        # 5. Добавляем Платеж и Штраф
        payment = Payment(order_id=order.id, amount=2000, payment_type="Income", method="Card") # Предоплата
        fine = Fine(order_id=order.id, violation_type="Speeding", amount=500, issue_date=date.today(), is_paid=False)
        
        session.add(payment)
        session.add(fine)
        session.commit()
        
        print("Тестовые данные добавлены!")

def run_queries():
    """Примеры выборок (Queries)"""
    with Session(engine) as session:
        print("\n--- ЗАПРОС 1: Доступные автомобили Бизнес-класса ---")
        # Join двух таблиц: Vehicle и CarModel
        statement = select(Vehicle, CarModel).where(Vehicle.model_id == CarModel.id).where(Vehicle.status == "Available").where(CarModel.car_class == "Business")
        results = session.exec(statement).all()
        for vehicle, model in results:
            print(f"Авто: {model.brand} {model.model_name}, Госномер: {vehicle.license_plate}, Цвет: {vehicle.color}")

        print("\n--- ЗАПРОС 2: Активные заказы клиента Иванов И.И. ---")
        statement = select(RentalOrder).join(Client).where(Client.full_name == "Иванов Иван Иванович").where(RentalOrder.order_status == "Open")
        orders = session.exec(statement).all()
        for order in orders:
            # Благодаря Relationship мы можем обращаться к связанным объектам через точку
            print(f"Заказ №{order.id} | Авто: {order.vehicle.model.brand} {order.vehicle.model.model_name} | Долг клиента: {order.total_cost} руб.")
            
        print("\n--- ЗАПРОС 3: Финансовый отчет по заказу (Платежи и Штрафы) ---")
        # Пример работы со списком связанных объектов
        if orders:
            current_order = orders[0]
            print(f"Платежи по заказу {current_order.id}:")
            for p in current_order.payments:
                print(f" - {p.payment_date.strftime('%Y-%m-%d')}: {p.amount} руб. ({p.payment_type})")
            
            print(f"Штрафы по заказу {current_order.id}:")
            for f in current_order.fines:
                print(f" - {f.violation_type}: {f.amount} руб. (Оплачен: {f.is_paid})")

if __name__ == "__main__":
    # 1. Создаем таблицы
    create_db_and_tables()
    
    # 2. Наполняем данными
    seed_data()
    
    # 3. Выполняем запросы
    run_queries()
