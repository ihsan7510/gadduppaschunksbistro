from django.test import TestCase, Client
from django.urls import reverse
from core.models import Staff

class StaffLoginTests(TestCase):
    def setUp(self):
        # Create test staff members
        self.admin_staff = Staff.objects.create(
            name="Test Admin",
            role="admin",
            pin="1111",
            password="adminpassword",
            is_active=True
        )
        self.waiter_staff = Staff.objects.create(
            name="Test Waiter",
            role="waiter",
            pin="2222",
            password="waiterpassword",
            is_active=True
        )
        self.chef_staff = Staff.objects.create(
            name="Test Chef",
            role="chef",
            pin="3333",
            password="chefpassword",
            is_active=True
        )
        self.client = Client()

    def test_waiter_login_with_pin(self):
        response = self.client.post(reverse('waiter:login'), {'pin': '2222'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('waiter:tables'))
        self.assertEqual(int(self.client.session.get('waiter_id')), self.waiter_staff.pk)

    def test_waiter_login_with_password(self):
        response = self.client.post(reverse('waiter:login'), {'pin': 'waiterpassword'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('waiter:tables'))
        self.assertEqual(int(self.client.session.get('waiter_id')), self.waiter_staff.pk)

    def test_admin_waiter_login_redirect_to_dashboard(self):
        response = self.client.post(reverse('waiter:login'), {'pin': '1111'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('admin_panel:dashboard'))
        self.assertTrue(self.client.session.get('admin_logged_in'))

    def test_chef_waiter_login_redirect_to_kitchen(self):
        response = self.client.post(reverse('waiter:login'), {'pin': '3333'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('kitchen:orders'))
        self.assertTrue(self.client.session.get('kitchen_logged_in'))

    def test_kitchen_login_with_pin(self):
        response = self.client.post(reverse('kitchen:login'), {'password': '3333'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.session.get('kitchen_logged_in'))

    def test_kitchen_login_with_password(self):
        response = self.client.post(reverse('kitchen:login'), {'password': 'chefpassword'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.session.get('kitchen_logged_in'))

    def test_admin_login_with_pin(self):
        response = self.client.post(reverse('admin_panel:login'), {
            'username': 'Test Admin',
            'password': '1111'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.session.get('admin_logged_in'))

    def test_admin_login_with_password(self):
        response = self.client.post(reverse('admin_panel:login'), {
            'username': 'Test Admin',
            'password': 'adminpassword'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.session.get('admin_logged_in'))
