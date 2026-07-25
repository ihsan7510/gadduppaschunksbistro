"""
Seed script to populate demo data for the restaurant app.
Run: python seed_data.py
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant.settings')
django.setup()

from core.models import Staff, RestaurantTable, Category, MenuItem, InventoryItem, RestaurantSettings

print("🌱 Seeding restaurant data...")

# Restaurant Settings
settings, _ = RestaurantSettings.objects.get_or_create(pk=1)
settings.restaurant_name = "Spice Garden Restaurant"
settings.address = "123 Main Street, Chennai - 600001"
settings.phone = "+91 98765 43210"
settings.gstin = "33ABCDE1234F1Z5"
settings.tax_percent = 5.00
settings.footer_message = "Thank you for dining with us! Visit again! 😊"
settings.currency_symbol = "₹"
settings.save()
print("✅ Restaurant settings saved")

# Staff
staff_data = [
    {"name": "Ravi Kumar", "role": "admin", "phone": "9876543210", "pin": "1234"},
    {"name": "Priya Sharma", "role": "waiter", "phone": "9876543211", "pin": "2222"},
    {"name": "Amit Singh", "role": "waiter", "phone": "9876543212", "pin": "3333"},
    {"name": "Chef Ramesh", "role": "chef", "phone": "9876543213", "pin": "4444"},
    {"name": "Sneha Patel", "role": "cashier", "phone": "9876543214", "pin": "5555"},
]
for s in staff_data:
    Staff.objects.get_or_create(pin=s['pin'], defaults=s)
print(f"✅ {len(staff_data)} staff members created")

# Tables
for i in range(1, 13):
    loc = "Indoor" if i <= 8 else "Outdoor"
    RestaurantTable.objects.get_or_create(
        number=i,
        defaults={"capacity": 4, "location": loc}
    )
print("✅ 12 tables created")

# Categories & Menu Items
categories = [
    {"name": "Starters", "icon": "🥗", "sort_order": 1, "items": [
        {"name": "Paneer Tikka", "price": 220, "is_veg": True, "prep": 15, "desc": "Grilled paneer with spices"},
        {"name": "Chicken 65", "price": 280, "is_veg": False, "prep": 20, "desc": "Crispy spiced chicken"},
        {"name": "Veg Spring Roll", "price": 160, "is_veg": True, "prep": 12, "desc": "Crispy vegetable rolls"},
        {"name": "Chicken Tikka", "price": 320, "is_veg": False, "prep": 20, "desc": "Marinated chicken tikka"},
    ]},
    {"name": "Main Course", "icon": "🍛", "sort_order": 2, "items": [
        {"name": "Butter Chicken", "price": 380, "is_veg": False, "prep": 25, "desc": "Creamy tomato chicken curry"},
        {"name": "Dal Makhani", "price": 280, "is_veg": True, "prep": 20, "desc": "Slow-cooked black lentils"},
        {"name": "Paneer Butter Masala", "price": 320, "is_veg": True, "prep": 20, "desc": "Rich creamy paneer curry"},
        {"name": "Chicken Biryani", "price": 420, "is_veg": False, "prep": 30, "desc": "Aromatic basmati rice with chicken"},
        {"name": "Veg Biryani", "price": 320, "is_veg": True, "prep": 25, "desc": "Fragrant vegetable biryani"},
        {"name": "Fish Curry", "price": 450, "is_veg": False, "prep": 25, "desc": "Coastal style fish curry"},
    ]},
    {"name": "Breads", "icon": "🫓", "sort_order": 3, "items": [
        {"name": "Garlic Naan", "price": 60, "is_veg": True, "prep": 10, "desc": "Soft tandoor bread with garlic"},
        {"name": "Butter Roti", "price": 40, "is_veg": True, "prep": 8, "desc": "Whole wheat roti"},
        {"name": "Paratha", "price": 70, "is_veg": True, "prep": 10, "desc": "Layered flatbread"},
    ]},
    {"name": "Beverages", "icon": "🥤", "sort_order": 4, "items": [
        {"name": "Mango Lassi", "price": 120, "is_veg": True, "prep": 5, "desc": "Sweet mango yogurt drink"},
        {"name": "Masala Chai", "price": 60, "is_veg": True, "prep": 5, "desc": "Spiced Indian tea"},
        {"name": "Cold Coffee", "price": 150, "is_veg": True, "prep": 5, "desc": "Chilled coffee blend"},
        {"name": "Fresh Lime Soda", "price": 80, "is_veg": True, "prep": 3, "desc": "Refreshing lime drink"},
    ]},
    {"name": "Desserts", "icon": "🍮", "sort_order": 5, "items": [
        {"name": "Gulab Jamun", "price": 100, "is_veg": True, "prep": 5, "desc": "Soft milk dumplings in syrup"},
        {"name": "Ice Cream (2 scoop)", "price": 140, "is_veg": True, "prep": 3, "desc": "Choice of flavors"},
        {"name": "Rasgulla", "price": 110, "is_veg": True, "prep": 5, "desc": "Soft cottage cheese balls"},
    ]},
]

for cat_data in categories:
    cat, _ = Category.objects.get_or_create(
        name=cat_data['name'],
        defaults={"icon": cat_data['icon'], "sort_order": cat_data['sort_order']}
    )
    for item_data in cat_data['items']:
        MenuItem.objects.get_or_create(
            name=item_data['name'],
            defaults={
                "category": cat,
                "price": item_data['price'],
                "is_veg": item_data['is_veg'],
                "preparation_time": item_data['prep'],
                "description": item_data['desc'],
                "is_available": True,
            }
        )
print(f"✅ Menu categories and items created")

# Inventory
inventory_items = [
    {"name": "Chicken", "unit": "kg", "quantity": 20, "threshold": 5, "cost": 280},
    {"name": "Basmati Rice", "unit": "kg", "quantity": 50, "threshold": 10, "cost": 80},
    {"name": "Paneer", "unit": "kg", "quantity": 8, "threshold": 2, "cost": 320},
    {"name": "Tomatoes", "unit": "kg", "quantity": 15, "threshold": 3, "cost": 40},
    {"name": "Onions", "unit": "kg", "quantity": 20, "threshold": 5, "cost": 35},
    {"name": "Cooking Oil", "unit": "L", "quantity": 10, "threshold": 3, "cost": 120},
    {"name": "Butter", "unit": "kg", "quantity": 4, "threshold": 1, "cost": 480},
    {"name": "Milk", "unit": "L", "quantity": 15, "threshold": 5, "cost": 60},
    {"name": "Wheat Flour", "unit": "kg", "quantity": 25, "threshold": 5, "cost": 45},
    {"name": "Fish", "unit": "kg", "quantity": 3, "threshold": 2, "cost": 350},
    {"name": "Sugar", "unit": "kg", "quantity": 10, "threshold": 2, "cost": 50},
    {"name": "Tea Leaves", "unit": "g", "quantity": 500, "threshold": 100, "cost": 2},
]
for inv in inventory_items:
    InventoryItem.objects.get_or_create(
        name=inv['name'],
        defaults={
            "unit": inv['unit'], "quantity": inv['quantity'],
            "low_stock_threshold": inv['threshold'], "cost_per_unit": inv['cost']
        }
    )
print(f"✅ {len(inventory_items)} inventory items created")

print("\n🎉 Demo data seeded successfully!")
print("\n📋 Login credentials:")
print("   Admin:   username=admin  password=admin123")
print("   Waiter:  PINs → Priya: 2222, Amit: 3333")
print("   Kitchen: password=kitchen123")
print("   TV:      No login required")
print("\n🚀 Start the server: python manage.py runserver")
