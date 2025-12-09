from fastapi import FastAPI, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional

# Импортируем настройки БД и Модели
from database import create_db_and_tables, get_session
from models import (
    CarModel, Vehicle, Client, Employee, RentalOrder, 
    Maintenance, Fine, Payment, InsurancePolicy, Review
)

app = FastAPI(
    title="Car Rental System API",
    description="Полный API для управления системой проката автомобилей (10 таблиц)",
    version="2.0.0"
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем всем (для тестов)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 1. СПРАВОЧНИК МОДЕЛЕЙ (CarModel)
# ==========================================
TAG_MODELS = "1. Справочник моделей"

@app.get("/models/", response_model=List[CarModel], tags=[TAG_MODELS], summary="Список всех моделей")
def get_car_models(session: Session = Depends(get_session)):
    """Получить список всех марок и моделей автомобилей с ценами."""
    return session.exec(select(CarModel)).all()

@app.post("/models/", response_model=CarModel, tags=[TAG_MODELS], summary="Добавить новую модель")
def create_car_model(model: CarModel, session: Session = Depends(get_session)):
    """Создать новую модель в справочнике (например, Kia Rio)."""
    session.add(model)
    session.commit()
    session.refresh(model)
    return model

@app.delete("/models/{model_id}", tags=[TAG_MODELS], summary="Удалить модель")
def delete_car_model(model_id: int, session: Session = Depends(get_session)):
    model = session.get(CarModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    
    # Проверка зависимостей
    if session.exec(select(Vehicle).where(Vehicle.model_id == model_id)).first():
        raise HTTPException(status_code=400, detail="Нельзя удалить модель: в базе есть автомобили этой модели.")

    session.delete(model)
    session.commit()
    return {"ok": True, "message": "Модель удалена"}


@app.put("/models/{model_id}", response_model=CarModel, tags=[TAG_MODELS], summary="Изменить модель")
def update_car_model(model_id: int, model_data: CarModel, session: Session = Depends(get_session)):
    db_model = session.get(CarModel, model_id)
    if not db_model:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    
    # Обновляем только переданные поля
    model_dict = model_data.dict(exclude_unset=True)
    for key, value in model_dict.items():
        setattr(db_model, key, value)
        
    session.add(db_model)
    session.commit()
    session.refresh(db_model)
    return db_model


# ==========================================
# 2. АВТОМОБИЛИ (Vehicle)
# ==========================================
TAG_VEHICLES = "2. Автомобили"

@app.get("/vehicles/", response_model=List[Vehicle], tags=[TAG_VEHICLES], summary="Список автомобилей")
def get_vehicles(status: Optional[str] = None, session: Session = Depends(get_session)):
    statement = select(Vehicle)
    if status:
        statement = statement.where(Vehicle.status == status)
    return session.exec(statement).all()

@app.post("/vehicles/", response_model=Vehicle, tags=[TAG_VEHICLES], summary="Добавить автомобиль")
def create_vehicle(vehicle: Vehicle, session: Session = Depends(get_session)):
    session.add(vehicle)
    session.commit()
    session.refresh(vehicle)
    return vehicle

@app.delete("/vehicles/{vehicle_id}", tags=[TAG_VEHICLES], summary="Удалить автомобиль")
def delete_vehicle(vehicle_id: int, session: Session = Depends(get_session)):
    vehicle = session.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    
    has_orders = session.exec(select(RentalOrder).where(RentalOrder.vehicle_id == vehicle_id)).first()
    has_maintenance = session.exec(select(Maintenance).where(Maintenance.vehicle_id == vehicle_id)).first()
    has_insurance = session.exec(select(InsurancePolicy).where(InsurancePolicy.vehicle_id == vehicle_id)).first()

    if has_orders or has_maintenance or has_insurance:
        raise HTTPException(
            status_code=400, 
            detail="Нельзя удалить авто: существуют связанные заказы, записи о ремонте или страховки."
        )

    session.delete(vehicle)
    session.commit()
    return {"ok": True}

@app.put("/vehicles/{vehicle_id}", response_model=Vehicle, tags=[TAG_VEHICLES], summary="Изменить данные авто")
def update_vehicle(vehicle_id: int, vehicle_data: Vehicle, session: Session = Depends(get_session)):
    db_vehicle = session.get(Vehicle, vehicle_id)
    if not db_vehicle:
        raise HTTPException(status_code=404, detail="Авто не найдено")
        
    vehicle_dict = vehicle_data.dict(exclude_unset=True)
    for key, value in vehicle_dict.items():
        setattr(db_vehicle, key, value)
        
    session.add(db_vehicle)
    session.commit()
    session.refresh(db_vehicle)
    return db_vehicle


# ==========================================
# 3. КЛИЕНТЫ (Client)
# ==========================================
TAG_CLIENTS = "3. Клиенты"

@app.get("/clients/", response_model=List[Client], tags=[TAG_CLIENTS], summary="Список клиентов")
def get_clients(session: Session = Depends(get_session)):
    return session.exec(select(Client)).all()

@app.post("/clients/", response_model=Client, tags=[TAG_CLIENTS], summary="Регистрация клиента")
def create_client(client: Client, session: Session = Depends(get_session)):
    session.add(client)
    session.commit()
    session.refresh(client)
    return client

@app.delete("/clients/{client_id}", tags=[TAG_CLIENTS], summary="Удалить клиента")
def delete_client(client_id: int, session: Session = Depends(get_session)):
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    if session.exec(select(RentalOrder).where(RentalOrder.client_id == client_id)).first():
        raise HTTPException(status_code=400, detail="Нельзя удалить клиента: у него есть история заказов.")

    session.delete(client)
    session.commit()
    return {"ok": True}


@app.put("/clients/{client_id}", response_model=Client, tags=[TAG_CLIENTS], summary="Изменить данные клиента")
def update_client(client_id: int, client_data: Client, session: Session = Depends(get_session)):
    db_client = session.get(Client, client_id)
    if not db_client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
        
    client_dict = client_data.dict(exclude_unset=True)
    for key, value in client_dict.items():
        setattr(db_client, key, value)
        
    session.add(db_client)
    session.commit()
    session.refresh(db_client)
    return db_client

# ==========================================
# 4. СОТРУДНИКИ (Employee)
# ==========================================
TAG_EMPLOYEES = "4. Сотрудники"

@app.get("/employees/", response_model=List[Employee], tags=[TAG_EMPLOYEES], summary="Список сотрудников")
def get_employees(session: Session = Depends(get_session)):
    return session.exec(select(Employee)).all()

@app.post("/employees/", response_model=Employee, tags=[TAG_EMPLOYEES], summary="Добавить сотрудника")
def create_employee(emp: Employee, session: Session = Depends(get_session)):
    session.add(emp)
    session.commit()
    session.refresh(emp)
    return emp

@app.delete("/employees/{emp_id}", tags=[TAG_EMPLOYEES], summary="Уволить сотрудника")
def delete_employee(emp_id: int, session: Session = Depends(get_session)):
    emp = session.get(Employee, emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    
    if session.exec(select(RentalOrder).where(RentalOrder.employee_id == emp_id)).first():
        raise HTTPException(status_code=400, detail="Нельзя удалить сотрудника: на него оформлены заказы.")

    session.delete(emp)
    session.commit()
    return {"ok": True}


@app.put("/employees/{emp_id}", response_model=Employee, tags=[TAG_EMPLOYEES], summary="Изменить данные сотрудника")
def update_employee(emp_id: int, emp_data: Employee, session: Session = Depends(get_session)):
    db_emp = session.get(Employee, emp_id)
    if not db_emp:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
        
    emp_dict = emp_data.dict(exclude_unset=True)
    for key, value in emp_dict.items():
        setattr(db_emp, key, value)
        
    session.add(db_emp)
    session.commit()
    session.refresh(db_emp)
    return db_emp

# ==========================================
# 5. ЗАКАЗЫ (RentalOrder)
# ==========================================
TAG_ORDERS = "5. Заказы"

@app.get("/orders/", response_model=List[RentalOrder], tags=[TAG_ORDERS], summary="Все заказы")
def get_orders(session: Session = Depends(get_session)):
    return session.exec(select(RentalOrder)).all()

@app.post("/orders/", response_model=RentalOrder, tags=[TAG_ORDERS], summary="Создать заказ")
def create_order(order: RentalOrder, session: Session = Depends(get_session)):
    # Проверка доступности машины
    vehicle = session.get(Vehicle, order.vehicle_id)
    if not vehicle or vehicle.status != "Available":
        raise HTTPException(status_code=400, detail="Машина не найдена или занята")
    
    # Меняем статус машины
    vehicle.status = "Rented"
    session.add(vehicle)
    
    session.add(order)
    session.commit()
    session.refresh(order)
    return order

@app.delete("/orders/{order_id}", tags=[TAG_ORDERS], summary="Удалить заказ")
def delete_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(RentalOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # Проверяем, есть ли связанные финансовые записи
    has_payments = session.exec(select(Payment).where(Payment.order_id == order_id)).first()
    has_fines = session.exec(select(Fine).where(Fine.order_id == order_id)).first()
    has_reviews = session.exec(select(Review).where(Review.order_id == order_id)).first()

    if has_payments or has_fines or has_reviews:
        raise HTTPException(
            status_code=400, 
            detail="Нельзя удалить заказ, так как по нему есть платежи, штрафы или отзывы. Удалите их сначала."
        )
    
    # Если заказ активен, нужно освободить машину перед удалением (опционально)
    if order.order_status == "Open":
        vehicle = session.get(Vehicle, order.vehicle_id)
        if vehicle and vehicle.status == "Rented":
            vehicle.status = "Available"
            session.add(vehicle)

    session.delete(order)
    session.commit()
    return {"ok": True}


@app.put("/orders/{order_id}", response_model=RentalOrder, tags=[TAG_ORDERS], summary="Редактировать заказ")
def update_order(order_id: int, order_data: RentalOrder, session: Session = Depends(get_session)):
    db_order = session.get(RentalOrder, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
        
    order_dict = order_data.dict(exclude_unset=True)
    for key, value in order_dict.items():
        setattr(db_order, key, value)
        
    session.add(db_order)
    session.commit()
    session.refresh(db_order)
    return db_order

# ==========================================
# 6. ОБСЛУЖИВАНИЕ (Maintenance)
# ==========================================
TAG_MAINTENANCE = "6. Обслуживание"

@app.get("/maintenance/", response_model=List[Maintenance], tags=[TAG_MAINTENANCE], summary="История ремонтов")
def get_maintenance(session: Session = Depends(get_session)):
    return session.exec(select(Maintenance)).all()

@app.post("/maintenance/", response_model=Maintenance, tags=[TAG_MAINTENANCE], summary="Запись на ремонт")
def create_maintenance(record: Maintenance, session: Session = Depends(get_session)):
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@app.delete("/maintenance/{record_id}", tags=[TAG_MAINTENANCE], summary="Удалить запись о ремонте")
def delete_maintenance(record_id: int, session: Session = Depends(get_session)):
    rec = session.get(Maintenance, record_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    session.delete(rec)
    session.commit()
    return {"ok": True}

@app.put("/maintenance/{record_id}", response_model=Maintenance, tags=[TAG_MAINTENANCE], summary="Изменить запись ремонта")
def update_maintenance(record_id: int, rec_data: Maintenance, session: Session = Depends(get_session)):
    db_rec = session.get(Maintenance, record_id)
    if not db_rec:
        raise HTTPException(status_code=404, detail="Запись не найдена")
        
    rec_dict = rec_data.dict(exclude_unset=True)
    for key, value in rec_dict.items():
        setattr(db_rec, key, value)
        
    session.add(db_rec)
    session.commit()
    session.refresh(db_rec)
    return db_rec

# ==========================================
# 7. ШТРАФЫ (Fine)
# ==========================================
TAG_FINES = "7. Штрафы"

@app.get("/fines/", response_model=List[Fine], tags=[TAG_FINES], summary="Список штрафов")
def get_fines(session: Session = Depends(get_session)):
    return session.exec(select(Fine)).all()

@app.post("/fines/", response_model=Fine, tags=[TAG_FINES], summary="Выписать штраф")
def create_fine(fine: Fine, session: Session = Depends(get_session)):
    session.add(fine)
    session.commit()
    session.refresh(fine)
    return fine

@app.delete("/fines/{fine_id}", tags=[TAG_FINES], summary="Удалить штраф")
def delete_fine(fine_id: int, session: Session = Depends(get_session)):
    fine = session.get(Fine, fine_id)
    if not fine:
        raise HTTPException(status_code=404, detail="Штраф не найден")
    session.delete(fine)
    session.commit()
    return {"ok": True}

@app.put("/fines/{fine_id}", response_model=Fine, tags=[TAG_FINES], summary="Изменить штраф")
def update_fine(fine_id: int, fine_data: Fine, session: Session = Depends(get_session)):
    db_fine = session.get(Fine, fine_id)
    if not db_fine:
        raise HTTPException(status_code=404, detail="Штраф не найден")
        
    fine_dict = fine_data.dict(exclude_unset=True)
    for key, value in fine_dict.items():
        setattr(db_fine, key, value)
        
    session.add(db_fine)
    session.commit()
    session.refresh(db_fine)
    return db_fine

# ==========================================
# 8. ПЛАТЕЖИ (Payment)
# ==========================================
TAG_PAYMENTS = "8. Платежи"

@app.get("/payments/", response_model=List[Payment], tags=[TAG_PAYMENTS], summary="История транзакций")
def get_payments(session: Session = Depends(get_session)):
    return session.exec(select(Payment)).all()

@app.post("/payments/", response_model=Payment, tags=[TAG_PAYMENTS], summary="Провести платеж")
def create_payment(payment: Payment, session: Session = Depends(get_session)):
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment

@app.delete("/payments/{payment_id}", tags=[TAG_PAYMENTS], summary="Отменить платеж")
def delete_payment(payment_id: int, session: Session = Depends(get_session)):
    payment = session.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Платеж не найден")
    session.delete(payment)
    session.commit()
    return {"ok": True}

@app.put("/payments/{payment_id}", response_model=Payment, tags=[TAG_PAYMENTS], summary="Изменить платеж")
def update_payment(payment_id: int, payment_data: Payment, session: Session = Depends(get_session)):
    db_payment = session.get(Payment, payment_id)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Платеж не найден")
        
    payment_dict = payment_data.dict(exclude_unset=True)
    for key, value in payment_dict.items():
        setattr(db_payment, key, value)
        
    session.add(db_payment)
    session.commit()
    session.refresh(db_payment)
    return db_payment

# ==========================================
# 9. СТРАХОВКА (InsurancePolicy)
# ==========================================
TAG_INSURANCE = "9. Страховка"

@app.get("/insurance/", response_model=List[InsurancePolicy], tags=[TAG_INSURANCE], summary="Все полисы")
def get_insurance(session: Session = Depends(get_session)):
    return session.exec(select(InsurancePolicy)).all()

@app.post("/insurance/", response_model=InsurancePolicy, tags=[TAG_INSURANCE], summary="Добавить страховку")
def create_insurance(policy: InsurancePolicy, session: Session = Depends(get_session)):
    session.add(policy)
    session.commit()
    session.refresh(policy)
    return policy

@app.delete("/insurance/{policy_id}", tags=[TAG_INSURANCE], summary="Удалить полис")
def delete_insurance(policy_id: int, session: Session = Depends(get_session)):
    policy = session.get(InsurancePolicy, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Полис не найден")
    session.delete(policy)
    session.commit()
    return {"ok": True}

@app.put("/insurance/{policy_id}", response_model=InsurancePolicy, tags=[TAG_INSURANCE], summary="Изменить полис")
def update_insurance(policy_id: int, policy_data: InsurancePolicy, session: Session = Depends(get_session)):
    db_policy = session.get(InsurancePolicy, policy_id)
    if not db_policy:
        raise HTTPException(status_code=404, detail="Полис не найден")
        
    policy_dict = policy_data.dict(exclude_unset=True)
    for key, value in policy_dict.items():
        setattr(db_policy, key, value)
        
    session.add(db_policy)
    session.commit()
    session.refresh(db_policy)
    return db_policy

# ==========================================
# 10. ОТЗЫВЫ (Review)
# ==========================================
TAG_REVIEWS = "10. Отзывы"

@app.get("/reviews/", response_model=List[Review], tags=[TAG_REVIEWS], summary="Все отзывы")
def get_reviews(session: Session = Depends(get_session)):
    return session.exec(select(Review)).all()

@app.post("/reviews/", response_model=Review, tags=[TAG_REVIEWS], summary="Оставить отзыв")
def create_review(review: Review, session: Session = Depends(get_session)):
    session.add(review)
    session.commit()
    session.refresh(review)
    return review

@app.delete("/reviews/{review_id}", tags=[TAG_REVIEWS], summary="Удалить отзыв")
def delete_review(review_id: int, session: Session = Depends(get_session)):
    review = session.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    session.delete(review)
    session.commit()
    return {"ok": True}

@app.put("/reviews/{review_id}", response_model=Review, tags=[TAG_REVIEWS], summary="Изменить отзыв")
def update_review(review_id: int, review_data: Review, session: Session = Depends(get_session)):
    db_review = session.get(Review, review_id)
    if not db_review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
        
    review_dict = review_data.dict(exclude_unset=True)
    for key, value in review_dict.items():
        setattr(db_review, key, value)
        
    session.add(db_review)
    session.commit()
    session.refresh(db_review)
    return db_review
