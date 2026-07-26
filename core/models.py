"""
Core models for the Restaurant Billing App.
Shared across all modules: Admin, Waiter, Kitchen, TV Display.
"""

from django.db import models
from django.utils import timezone


class Staff(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('waiter', 'Waiter'),
        ('chef', 'Chef'),
        ('cashier', 'Cashier'),
    ]
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True)
    pin = models.CharField(max_length=6)  # 4-6 digit PIN for quick login
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Staff'


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('on_duty', 'On Duty'),
    ]
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now)
    clock_in = models.TimeField(null=True, blank=True)
    clock_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='absent')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.staff.name} - {self.date} ({self.get_status_display()})"

    class Meta:
        unique_together = ['staff', 'date']
        ordering = ['-date']


class RestaurantTable(models.Model):
    STATUS_CHOICES = [
        ('free', 'Free'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
        ('cleaning', 'Cleaning'),
    ]
    number = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=50, blank=True)  # e.g., "Window Table"
    capacity = models.PositiveIntegerField(default=4)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='free')
    location = models.CharField(max_length=50, blank=True)  # e.g., "Indoor", "Outdoor"
    is_parcel = models.BooleanField(default=False)

    def __str__(self):
        if self.is_parcel:
            return f"Parcel {self.number} ({self.get_status_display()})"
        return f"Table {self.number} ({self.get_status_display()})"

    @property
    def display_name(self):
        if self.is_parcel:
            return f"Parcel {self.number}"
        return f"Table {self.number}"

    class Meta:
        ordering = ['number']


class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='🍽️')  # emoji icon
    sort_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Categories'


class MenuItem(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='items')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_veg = models.BooleanField(default=True)
    preparation_time = models.PositiveIntegerField(default=15, help_text='Minutes')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - ₹{self.price}"

    class Meta:
        ordering = ['category', 'name']


class InventoryItem(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('L', 'Litre'),
        ('ml', 'Millilitre'),
        ('pcs', 'Pieces'),
        ('dozen', 'Dozen'),
        ('packet', 'Packet'),
    ]
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    low_stock_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=5)
    cost_per_unit = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    supplier = models.CharField(max_length=200, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"

    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold

    class Meta:
        ordering = ['name']


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('served', 'Served'),
        ('billed', 'Billed'),
        ('cancelled', 'Cancelled'),
    ]
    table = models.ForeignKey(RestaurantTable, on_delete=models.PROTECT, related_name='orders')
    waiter = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, related_name='orders_taken')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    order_number = models.CharField(max_length=20, unique=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.order_number} - Table {self.table.number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import datetime
            today = datetime.date.today()
            count = Order.objects.filter(created_at__date=today).count() + 1
            self.order_number = f"ORD{today.strftime('%y%m%d')}{count:03d}"
        super().save(*args, **kwargs)

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    ITEM_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('served', 'Served'),
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)  # snapshot at time of order
    notes = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=ITEM_STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"

    @property
    def subtotal(self):
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.menu_item.price
        super().save(*args, **kwargs)


class Bill(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
        ('online', 'Online'),
    ]
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name='bill')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bill for Order #{self.order.order_number} - ₹{self.total}"

    def save(self, *args, **kwargs):
        self.tax_amount = (self.subtotal * self.tax_percent) / 100
        self.discount_amount = (self.subtotal * self.discount_percent) / 100
        self.total = self.subtotal + self.tax_amount - self.discount_amount
        super().save(*args, **kwargs)


class RestaurantSettings(models.Model):
    """Singleton model for restaurant configuration."""
    restaurant_name = models.CharField(max_length=200, default='My Restaurant')
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    gstin = models.CharField(max_length=50, blank=True)
    logo = models.ImageField(upload_to='restaurant/', blank=True, null=True)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    printer_mac = models.CharField(max_length=255, blank=True, help_text='Bluetooth printer MAC address')
    printer_port = models.CharField(max_length=50, blank=True, help_text='USB printer port e.g. /dev/usb/lp0')
    footer_message = models.CharField(max_length=200, default='Thank you for dining with us!')
    currency_symbol = models.CharField(max_length=5, default='₹')

    def __str__(self):
        return self.restaurant_name

    class Meta:
        verbose_name = 'Restaurant Settings'
        verbose_name_plural = 'Restaurant Settings'
