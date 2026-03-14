from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

import models, schemas
from database import engine, get_db

#crea base de datos
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Inventory Management API",
    description="Products · Customers · Orders · Inventory",
    version="2.0.0",
)


# ──────────────────────────────────────────────────────────────────────────────
# PRODUCTS
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/products", response_model=List[schemas.ProductOut], tags=["Products"])
def list_products(db: Session = Depends(get_db)):
    """All active products with their current stock level."""
    products = (
        db.query(models.Product)
        .filter(models.Product.is_active == True)
        .order_by(models.Product.name)
        .all()
    )
    return [_product_out(p) for p in products]


@app.get("/products/{product_id}", response_model=schemas.ProductOut, tags=["Products"])
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _product_out(product)


# ──────────────────────────────────────────────────────────────────────────────
# CUSTOMERS
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/customers", response_model=List[schemas.CustomerOut], tags=["Customers"])
def list_customers(db: Session = Depends(get_db)):
    return db.query(models.Customer).order_by(models.Customer.name).all()


@app.post("/customers", response_model=schemas.CustomerOut,
          status_code=status.HTTP_201_CREATED, tags=["Customers"])
def create_customer(body: schemas.CustomerCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Customer).filter(
        models.Customer.email == body.email
    ).first()
    if existing:
        raise HTTPException(status_code=409,
                            detail="A customer with that email already exists.")

    customer = models.Customer(**body.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer



# ORDERS


@app.post("/orders", response_model=schemas.OrderOut,
          status_code=status.HTTP_201_CREATED, tags=["Orders"])
def create_order(body: schemas.OrderCreate, db: Session = Depends(get_db)):

    # Validar al cliente 
    customer = db.query(models.Customer).filter(
        models.Customer.id == body.customer_id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail=(f"Customer ID {body.customer_id} is not registered. "
                    "Please create the customer first.")
        )
    if not customer.is_active:
        raise HTTPException(
            status_code=400,
            detail="Customer account is inactive and cannot place orders."
        )

    # Validar productos e inventario 
    issues   = []  
    resolved = {}   

    for item in body.items:
        product = db.query(models.Product).filter(
            models.Product.id == item.product_id
        ).first()

        if not product:
            issues.append(f"Product ID {item.product_id} does not exist.")
            continue
        if not product.is_active:
            issues.append(f"Product '{product.name}' is currently unavailable.")
            continue

        stock = float(product.inventory.quantity) if product.inventory else 0.0
        if item.quantity > stock:
            issues.append(
                f"Insufficient stock for '{product.name}': "
                f"requested {item.quantity}, available {stock}."
            )
            continue

        resolved[item.product_id] = (product, item.quantity)

    # Creacion de ordenes
    if issues:
        order = models.Order(
            customer_id=body.customer_id,
            status="rejected",
            rejection_reason=" | ".join(issues),
        )
        db.add(order)
        db.flush()   # se obtiene el id antes de procesar la orden

        for item in body.items:
            prod_tuple = resolved.get(item.product_id)
            unit_price = float(prod_tuple[0].price) if prod_tuple else 0.0
            db.add(models.OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=unit_price,
            ))

    else:
        # aprobada
        total = sum(
            qty * float(prod.price)
            for prod, qty in resolved.values()
        )
        order = models.Order(
            customer_id=body.customer_id,
            status="approved",
            total_amount=total,
        )
        db.add(order)
        db.flush()

        for product, qty in resolved.values():
            db.add(models.OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=qty,
                unit_price=float(product.price),
            ))

            # se modifica el inventario
            product.inventory.quantity = float(product.inventory.quantity) - qty

            # se registra el movimiento
            db.add(models.InventoryMovement(
                product_id=product.id,
                order_id=order.id,
                movement_type="out",
                quantity=qty,
                notes=f"Sold via order #{order.id}",
            ))

    db.commit()
    db.refresh(order)
    return _order_out(order)


@app.get("/orders", response_model=List[schemas.OrderOut], tags=["Orders"])
def list_orders(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List orders. Optional query param: ?status_filter=approved|rejected|pending"""
    query = db.query(models.Order).order_by(models.Order.created_at.desc())
    if status_filter:
        query = query.filter(models.Order.status == status_filter)
    return [_order_out(o) for o in query.all()]


@app.get("/orders/{order_id}", response_model=schemas.OrderOut, tags=["Orders"])
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _order_out(order)



# inventario


@app.get("/inventory", response_model=List[schemas.InventoryOut], tags=["Inventory"])
def list_inventory(db: Session = Depends(get_db)):
    rows = (
        db.query(models.Inventory)
        .join(models.Product)
        .order_by(models.Product.name)
        .all()
    )
    return [
        schemas.InventoryOut(
            product_id=inv.product_id,
            product_name=inv.product.name,
            quantity=float(inv.quantity),
            min_stock=float(inv.min_stock),
            unit=inv.product.unit,
            updated_at=inv.updated_at,
        )
        for inv in rows
    ]


@app.post("/inventory/adjust", tags=["Inventory"])
def adjust_inventory(body: schemas.AdjustmentIn, db: Session = Depends(get_db)):
    """
    Manually adjust stock.
    Positive quantity  → stock in  (new shipment, correction up).
    Negative quantity  → stock out (write-off, correction down).
    """
    product = db.query(models.Product).filter(
        models.Product.id == body.product_id,
        models.Product.is_active == True,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Active product not found.")

    inv = product.inventory
    if not inv:
        inv = models.Inventory(product_id=product.id, quantity=0)
        db.add(inv)
        db.flush()

    current   = float(inv.quantity)
    new_stock = current + body.quantity

    if new_stock < 0:
        raise HTTPException(
            status_code=400,
            detail=(f"Cannot reduce stock below 0. "
                    f"Current: {current}, adjustment: {body.quantity}.")
        )

    inv.quantity = new_stock

    db.add(models.InventoryMovement(
        product_id=product.id,
        movement_type="in" if body.quantity >= 0 else "out",
        quantity=abs(body.quantity),
        notes=body.notes or "Manual adjustment",
    ))

    db.commit()
    return {
        "message":        "Inventory adjusted successfully.",
        "product":        product.name,
        "previous_stock": current,
        "adjustment":     body.quantity,
        "new_stock":      new_stock,
    }


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS — ORM objects → Pydantic-friendly dicts
# ──────────────────────────────────────────────────────────────────────────────

def _product_out(p: models.Product) -> schemas.ProductOut:
    return schemas.ProductOut(
        id=p.id,
        name=p.name,
        description=p.description,
        price=float(p.price),
        unit=p.unit,
        is_active=p.is_active,
        stock=float(p.inventory.quantity) if p.inventory else 0.0,
    )


def _order_out(o: models.Order) -> schemas.OrderOut:
    return schemas.OrderOut(
        id=o.id,
        customer_id=o.customer_id,
        customer_name=o.customer.name,
        status=o.status,
        rejection_reason=o.rejection_reason,
        total_amount=float(o.total_amount) if o.total_amount else None,
        created_at=o.created_at,
        items=[
            schemas.OrderItemOut(
                product_id=item.product_id,
                product_name=item.product.name,
                quantity=float(item.quantity),
                unit_price=float(item.unit_price),
                subtotal=float(item.quantity) * float(item.unit_price),
            )
            for item in o.items
        ],
    )