from enum import Enum
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, Enum as SQLEnum, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

# ==========================================
# 1. MA'LUMOTLAR BAZASI SOZLAMALARI (SQLite)
# ==========================================
DATABASE_URL = "sqlite:///./agritech.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Bazadan sessiya olish uchun yordamchi funksiya
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 2. DATABASE MODELLARI (TABLES)
# ==========================================

class UserRole(str, Enum):
    FARMER = "farmer"
    BUYER = "buyer"  # Restoran / Supermarket

class OrderStatus(str, Enum):
    PENDING = "kutilmoqda"
    ESCROW_LOCKED = "muzlatilgan"  # Pul Escrow hisobida
    DELIVERED = "yetkazildi"
    COMPLETED = "yakunlandi"      # Pul fermerga o'tkazildi
    CANCELLED = "bekor_qilindi"

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.FARMER)
    region = Column(String)

    products = relationship("ProductDB", back_populates="farmer")

class ProductDB(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False) # Masalan: Sabzavotlar, Mevalar
    price_per_kg = Column(Float, nullable=False)
    available_qty = Column(Float, nullable=False) # Qancha kg mavjud
    farmer_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    farmer = relationship("UserDB", back_populates="products")

class OrderDB(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    buyer_id = Column(Integer, ForeignKey("users.id"))
    quantity_kg = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

# Bazadagi barcha jadvallarni yaratish
Base.metadata.create_all(bind=engine)

# ==========================================
# 3. PYDANTIC SCHEMAS (Validation & DTOs)
# ==========================================

class UserCreate(BaseModel):
    full_name: str
    phone: str
    role: UserRole
    region: str

class UserResponse(UserCreate):
    id: int
    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    title: str
    category: str
    price_per_kg: float = Field(gt=0, description="Narx 0 dan baland bo'lishi shart")
    available_qty: float = Field(gt=0)
    farmer_id: int

class ProductResponse(ProductCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    product_id: int
    buyer_id: int
    quantity_kg: float = Field(gt=0)

class OrderResponse(BaseModel):
    id: int
    product_id: int
    buyer_id: int
    quantity_kg: float
    total_price: float
    status: OrderStatus
    created_at: datetime
    class Config:
        from_attributes = True

# ==========================================
# 4. FASTAPI ILOVASI VA ENDPOINTLAR (API)
# ==========================================

app = FastAPI(
    title="AgriTech B2B API",
    description="Fermerlar va B2B xaridorlar uchun backend servisi",
    version="1.0.0"
)

# Frontend bilan ulana olishi uchun CORS sozlamalari
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "AgriTech B2B Platform API ishlamoqda!"}

# --- FOYDALANUVCHILAR (USERS) ---

@app.post("/api/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.phone == user.phone).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Ushbu telefon raqam ro'yxatdan o'tgan")
    
    new_user = UserDB(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# --- MAHSULOTLAR (PRODUCTS) ---

@app.post("/api/products/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    # Fermer borligini checks qilish
    farmer = db.query(UserDB).filter(UserDB.id == product.farmer_id, UserDB.role == UserRole.FARMER).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Fermer topilmadi")

    new_product = ProductDB(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@app.get("/api/products/", response_model=List[ProductResponse])
def get_products(category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(ProductDB)
    if category:
        query = query.filter(ProductDB.category == category)
    return query.all()

# --- BUYURTMALAR VA ESCROW (ORDERS) ---

@app.post("/api/orders/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    product = db.query(ProductDB).filter(ProductDB.id == order.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
    
    if product.available_qty < order.quantity_kg:
        raise HTTPException(status_code=400, detail="Omborda yetarli mahsulot yo'q")

    total_price = product.price_per_kg * order.quantity_kg
    
    # Buyurtma yaratish va statusini ESCROW_LOCKED (Pul muzlatildi) qilish
    new_order = OrderDB(
        product_id=order.product_id,
        buyer_id=order.buyer_id,
        quantity_kg=order.quantity_kg,
        total_price=total_price,
        status=OrderStatus.ESCROW_LOCKED
    )
    
    # Mahsulot hajmini kamaytirish
    product.available_qty -= order.quantity_kg

    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

@app.put("/api/orders/{order_id}/complete/", response_model=OrderResponse)
def complete_order(order_id: int, db: Session = Depends(get_db)):
    """Restoran mahsulotni qabul qilib olgach, Escrow pulini fermerga o'tkazishni tasdiqlaydi"""
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")

    if order.status != OrderStatus.ESCROW_LOCKED:
        raise HTTPException(status_code=400, detail="Buyurtma statusi noto'g'ri")

    order.status = OrderStatus.COMPLETED
    db.commit()
    db.refresh(order)
    return order