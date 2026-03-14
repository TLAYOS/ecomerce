from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, field_validator
 
 
# ── Customers ──────────────────────────────────────────────────────────────
 
class CustomerCreate(BaseModel):
    name:    str
    email:   EmailStr
    phone:   Optional[str] = None
    address: Optional[str] = None
 
 
class CustomerOut(BaseModel):
    id:         int
    name:       str
    email:      str
    phone:      Optional[str]
    address:    Optional[str]
    is_active:  bool
    created_at: datetime
 
    model_config = {"from_attributes": True}
 
 
# ── Products ───────────────────────────────────────────────────────────────
 
class ProductOut(BaseModel):
    id:          int
    name:        str
    description: Optional[str]
    price:       float
    unit:        str
    is_active:   bool
    stock:       float   # resolved from the inventory relationship
 
    model_config = {"from_attributes": True}
 
 
# ── Orders ─────────────────────────────────────────────────────────────────
 
class OrderItemIn(BaseModel):
    product_id: int
    quantity:   float
 
    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v):
        if v <= 0:
            raise ValueError("quantity must be greater than 0")
        return v
 
 
class OrderCreate(BaseModel):
    customer_id: int
    items:       List[OrderItemIn]
 
    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v):
        if not v:
            raise ValueError("order must contain at least one item")
        return v
 
 
class OrderItemOut(BaseModel):
    product_id:   int
    product_name: str
    quantity:     float
    unit_price:   float
    subtotal:     float
 
    model_config = {"from_attributes": True}
 
 
class OrderOut(BaseModel):
    id:               int
    customer_id:      int
    customer_name:    str
    status:           str
    rejection_reason: Optional[str]
    total_amount:     Optional[float]
    created_at:       datetime
    items:            List[OrderItemOut] = []
 
    model_config = {"from_attributes": True}
 
 
# ── Inventory ──────────────────────────────────────────────────────────────
 
class InventoryOut(BaseModel):
    product_id:   int
    product_name: str
    quantity:     float
    min_stock:    float
    unit:         str
    updated_at:   datetime
 
    model_config = {"from_attributes": True}
 
 
class AdjustmentIn(BaseModel):
    product_id: int
    quantity:   float    # positive = add, negative = remove
    notes:      Optional[str] = None