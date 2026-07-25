from django.test import TestCase, Client
from django.urls import reverse
from core.models import RestaurantTable, MenuItem, Category, Order, OrderItem

class CustomerSelfOrderTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Beverages", sort_order=1)
        self.table = RestaurantTable.objects.create(number=5, capacity=4, status="free")
        self.item = MenuItem.objects.create(
            name="Lemon Tea",
            category=self.category,
            price=25.00,
            is_available=True
        )

    def test_table_order_view(self):
        # Visit the table order page
        url = reverse('customer:table_order', kwargs={'table_number': self.table.number})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'customer/table_order.html')
        self.assertEqual(self.client.session.get('customer_table'), self.table.number)

    def test_place_order_success(self):
        # Set session table number first
        session = self.client.session
        session['customer_table'] = self.table.number
        session.save()

        # Submit order cart via POST
        url = reverse('customer:place_order')
        post_data = {
            f'qty_{self.item.pk}': 2,
            f'note_{self.item.pk}': 'Less sugar please',
            'order_notes': 'Deliver fast'
        }
        response = self.client.post(url, data=post_data)
        
        # Verify redirect to order-status page
        self.assertRedirects(response, reverse('customer:order_status'))

        # Verify Order is created in DB
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.table, self.table)
        self.assertIsNone(order.waiter)
        self.assertEqual(order.status, 'confirmed')

        # Verify OrderItem is created
        self.assertEqual(OrderItem.objects.count(), 1)
        order_item = OrderItem.objects.first()
        self.assertEqual(order_item.menu_item, self.item)
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.notes, 'Less sugar please')

        # Verify Table status is now occupied
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'occupied')
