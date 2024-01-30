from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from .models import Transaction, Wallet


class TransactionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="test_user")
        self.wallet1_rub = Wallet.objects.create(
            user=self.user, currency="RUB", balance=Decimal("100.00")
        )
        self.wallet2_rub = Wallet.objects.create(
            user=self.user, currency="RUB", balance=Decimal("200.00")
        )
        self.wallet3_usd = Wallet.objects.create(
            user=self.user, currency="USD", balance=Decimal("200.00")
        )

    def test_transaction_success(self):
        transaction = Transaction.objects.create(
            amount=Decimal("50.00"), sender=self.wallet1_rub, recipient=self.wallet2_rub
        )

        self.assertEqual(self.wallet1_rub.balance, Decimal("50.00"))
        self.assertEqual(self.wallet2_rub.balance, Decimal("250.00"))

    def test_transaction_self_transfer(self):
        with self.assertRaises(ValidationError):
            Transaction.objects.create(
                amount=Decimal("50.00"),
                sender=self.wallet1_rub,
                recipient=self.wallet1_rub,
            )

    def test_transaction_insufficient_funds(self):
        with self.assertRaises(ValidationError):
            Transaction.objects.create(
                amount=Decimal("150.00"),
                sender=self.wallet1_rub,
                recipient=self.wallet2_rub,
            )

    def test_transaction_different_currencies(self):
        with self.assertRaises(ValidationError):
            Transaction.objects.create(
                amount=Decimal("50.00"),
                sender=self.wallet1_rub,
                recipient=self.wallet3_usd,
            )

    def test_transaction_balance_not_changed_on_failure(self):
        try:
            Transaction.objects.create(
                amount=Decimal("150.00"),
                sender=self.wallet1_rub,
                recipient=self.wallet2_rub,
            )
        except ValidationError:
            self.assertEqual(self.wallet1_rub.balance, Decimal("100.00"))
            self.assertEqual(self.wallet2_rub.balance, Decimal("200.00"))


class CreateWalletViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )

    def test_create_wallet_success(self):
        url = reverse("create_wallet")

        data = {"user_id": self.user.id, "currency": "USD", "balance": "1000.00"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 201)
        self.assertTrue("id" in response.json())

    def test_create_wallet_invalid_data(self):
        url = reverse("create_wallet")

        data = {"currency": "USD", "balance": "1000.00"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 400)
        self.assertTrue("errors" in response.json())


class CreateTransactionViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="password123")
        self.user2 = User.objects.create_user(username="user2", password="password456")
        self.wallet1 = Wallet.objects.create(
            user=self.user1, currency="USD", balance=Decimal("1000.00")
        )
        self.wallet2 = Wallet.objects.create(
            user=self.user2, currency="USD", balance=Decimal("2000.00")
        )

    def test_create_transaction_success(self):
        url = reverse("create_transaction")

        data = {
            "sender_id": self.wallet1.id,
            "recipient_id": self.wallet2.id,
            "amount": Decimal("100.00"),
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 201)
        self.assertTrue("success" in response.json())

    def test_create_transaction_invalid_data(self):
        url = reverse("create_transaction")

        data = {"recipient_id": self.wallet2.id, "amount": Decimal("100.00")}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 400)
        self.assertTrue("error" in response.json())

    def test_create_transaction_sender_not_exists(self):
        url = reverse("create_transaction")

        data = {
            "sender_id": 9999,
            "recipient_id": self.wallet2.id,
            "amount": Decimal("100.00"),
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 400)
        self.assertTrue("error" in response.json())

    def test_create_transaction_recipient_not_exists(self):
        url = reverse("create_transaction")

        data = {
            "sender_id": self.wallet1.id,
            "recipient_id": 9999,
            "amount": Decimal("100.00"),
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 400)
        self.assertTrue("error" in response.json())

    def test_create_transaction_insufficient_balance(self):
        url = reverse("create_transaction")

        data = {
            "sender_id": self.wallet1.id,
            "recipient_id": self.wallet2.id,
            "amount": Decimal("1500.00"),  # Больше баланса отправителя
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 400)
        self.assertTrue("error" in response.json())
