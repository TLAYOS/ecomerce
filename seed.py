from database import SessionLocal, engine
import models
 
models.Base.metadata.create_all(bind=engine)
 
db = SessionLocal()
 
# ── Customers ────────────────────────────────────────────────
customers = [
    models.Customer(name="Alice García",  email="alice@example.com",  phone="555-0101", address="Av. Reforma 100, CDMX"),
    models.Customer(name="Bob Martínez",  email="bob@example.com",    phone="555-0102", address="Calle 5 de Mayo 200, MTY"),
    models.Customer(name="Carol López",   email="carol@example.com",  phone="555-0103", address="Blvd. Independencia 300, TRC"),
    models.Customer(name="David Sánchez", email="david@example.com",  phone="555-0104", address="Paseo Colón 400, GDL"),
]
db.add_all(customers)
db.flush()
 
# ── Products + Inventory ─────────────────────────────────────
catalog = [
    ("Laptop Pro 15",        "High-performance laptop 15\"", 25000.00, "unit", 10, 2),
    ("Wireless Mouse",       "Ergonomic wireless mouse",       450.00, "unit", 50, 5),
    ("USB-C Hub 7-in-1",     "Multi-port USB-C hub",           850.00, "unit", 30, 5),
    ("Mechanical Keyboard",  "TKL mechanical keyboard",       1800.00, "unit", 20, 3),
    ("27\" Monitor",         "4K IPS 27-inch monitor",       12000.00, "unit",  8, 2),
]
 
for name, desc, price, unit, qty, min_stock in catalog:
    product = models.Product(name=name, description=desc, price=price, unit=unit)
    db.add(product)
    db.flush()
 
    db.add(models.Inventory(product_id=product.id, quantity=qty, min_stock=min_stock))
    db.add(models.InventoryMovement(
        product_id=product.id,
        movement_type="in",
        quantity=qty,
        notes="Initial stock",
    ))
 
db.commit()
db.close()
print("✅  Sample data loaded successfully.")