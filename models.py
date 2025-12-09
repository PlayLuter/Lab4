from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from sqlmodel import SQLModel, Field, Relationship

# 1. CarModel (Справочник моделей)
class CarModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    brand: str
    model_name: str
    car_class: str = Field(alias="class") # В Python 'class' зарезервировано, в БД будет 'class'
    daily_rate: Decimal = Field(max_digits=10, decimal_places=2)
    deposit_amount: Decimal = Field(max_digits=10, decimal_places=2)
    
    vehicles: List["Vehicle"] = Relationship(back_populates="model")

# 2. Vehicle (Автомобиль)
class Vehicle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model_id: int = Field(foreign_key="carmodel.id")
    license_plate: str
    vin_code: str
    color: str
    current_mileage: int
    status: str  # Available, Rented, Maintenance
    
    model: Optional[CarModel] = Relationship(back_populates="vehicles")
    orders: List["RentalOrder"] = Relationship(back_populates="vehicle")
    insurance: List["InsurancePolicy"] = Relationship(back_populates="vehicle")
    maintenances: List["Maintenance"] = Relationship(back_populates="vehicle")

# 3. Client (Клиент)
class Client(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    driver_license_num: str
    passport_data: str
    phone: str
    birth_date: date
    rating: Decimal = Field(default=5.0, max_digits=3, decimal_places=2)
    is_blacklisted: bool = Field(default=False)
    
    orders: List["RentalOrder"] = Relationship(back_populates="client")

# 4. Employee (Сотрудник)
class Employee(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    position: str
    status: str = Field(default="Active") # Active, Fired, Vacation, Sick, Maternity
    
    orders: List["RentalOrder"] = Relationship(back_populates="employee")

# 5. RentalOrder (Заказ)
class RentalOrder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="client.id")
    vehicle_id: int = Field(foreign_key="vehicle.id")
    employee_id: int = Field(foreign_key="employee.id")
    
    start_date: datetime
    end_date_planned: datetime
    end_date_actual: Optional[datetime] = None
    
    total_cost: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)
    payment_status: str # Paid, Unpaid, Partial
    deposit_returned: bool = Field(default=False)
    order_status: str # Open, Closed
    
    # Связи
    client: Optional[Client] = Relationship(back_populates="orders")
    vehicle: Optional[Vehicle] = Relationship(back_populates="orders")
    employee: Optional[Employee] = Relationship(back_populates="orders")
    payments: List["Payment"] = Relationship(back_populates="order")
    fines: List["Fine"] = Relationship(back_populates="order")
    review: Optional["Review"] = Relationship(back_populates="order")

# 6. Maintenance (Ремонт)
class Maintenance(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    vehicle_id: int = Field(foreign_key="vehicle.id")
    start_date: date
    end_date: Optional[date] = None
    service_type: str
    cost: Decimal = Field(max_digits=10, decimal_places=2)
    description: Optional[str] = None
    
    vehicle: Optional[Vehicle] = Relationship(back_populates="maintenances")

# 7. Fine (Штраф)
class Fine(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="rentalorder.id")
    violation_type: str
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    is_paid: bool = Field(default=False)
    issue_date: date

    order: Optional[RentalOrder] = Relationship(back_populates="fines")

# 8. Payment (Платеж)
class Payment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="rentalorder.id")
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    payment_date: datetime
    payment_type: str
    method: str 
    
    order: Optional[RentalOrder] = Relationship(back_populates="payments")

# 9. InsurancePolicy (Страховка)
class InsurancePolicy(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    vehicle_id: int = Field(foreign_key="vehicle.id")
    policy_number: str
    insurance_company: str
    start_date: date
    end_date: date
    cost: Decimal = Field(max_digits=10, decimal_places=2)

    vehicle: Optional[Vehicle] = Relationship(back_populates="insurance")

# 10. Review (Отзыв)
class Review(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="rentalorder.id")
    car_rating: int
    client_rating: int
    comment: Optional[str] = None
    
    order: Optional[RentalOrder] = Relationship(back_populates="review")
