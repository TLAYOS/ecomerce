from sqlalchemy import (
    Boolean, Column, Integer, String, Text,
    DECIMAL, DateTime, Enum, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# AQUI SE CREAN LAS TABLAS, EN VEZ DE CREARLAS DIRECTAMENTE EN MYSQL, COMO SE MUESTRA A CONTINUACION 
 
 
class Customer(Base):
    __tablename__ = "customers"
 
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(150), unique=True, nullable=False, index=True)
    phone      = Column(String(20))
    address    = Column(Text)
    is_active  = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
 
    orders = relationship("Order", back_populates="customer")
 
 
class Product(Base):
    __tablename__ = "products"
 
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(150), nullable=False)
    description = Column(Text)
    price       = Column(DECIMAL(10, 2), nullable=False)
    unit        = Column(String(30), default="unit", nullable=False)
    is_active   = Column(Boolean, default=True, nullable=False)
    created_at  = Column(DateTime, server_default=func.now())
 
    inventory   = relationship("Inventory", back_populates="product", uselist=False)
    order_items = relationship("OrderItem", back_populates="product")
    movements   = relationship("InventoryMovement", back_populates="product")
 
 
class Inventory(Base):
    __tablename__ = "inventory"
 
    id         = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"),
                        unique=True, nullable=False)
    quantity   = Column(DECIMAL(10, 2), default=0, nullable=False)
    min_stock  = Column(DECIMAL(10, 2), default=0, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
 
    product = relationship("Product", back_populates="inventory")
 
 
class Order(Base):
    __tablename__ = "orders"
 
    id               = Column(Integer, primary_key=True, index=True)
    customer_id      = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status           = Column(
                           Enum("pending", "approved", "rejected"),
                           default="pending", nullable=False
                       )
    rejection_reason = Column(String(500))
    total_amount     = Column(DECIMAL(12, 2))
    created_at       = Column(DateTime, server_default=func.now())
    updated_at       = Column(DateTime, server_default=func.now(), onupdate=func.now())
 
    customer    = relationship("Customer", back_populates="orders")
    items       = relationship("OrderItem", back_populates="order",
                               cascade="all, delete-orphan")
    movements   = relationship("InventoryMovement", back_populates="order")
 
 
class OrderItem(Base):
    __tablename__ = "order_items"
 
    id         = Column(Integer, primary_key=True, index=True)
    order_id   = Column(Integer, ForeignKey("orders.id",   ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity   = Column(DECIMAL(10, 2), nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
 
    order   = relationship("Order",   back_populates="items")
    product = relationship("Product", back_populates="order_items")
 
 
class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
 
    id            = Column(Integer, primary_key=True, index=True)
    product_id    = Column(Integer, ForeignKey("products.id"), nullable=False)
    order_id      = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"),
                           nullable=True)
    movement_type = Column(Enum("in", "out", "adjustment"), nullable=False)
    quantity      = Column(DECIMAL(10, 2), nullable=False)
    notes         = Column(Text)
    created_at    = Column(DateTime, server_default=func.now())
 
    product = relationship("Product", back_populates="movements")
    order   = relationship("Order",   back_populates="movements")