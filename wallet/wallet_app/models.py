import logging

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models, transaction

logger = logging.getLogger(__name__)


class Wallet(models.Model):
    CURRENCY_CHOICES = (
        ("RUB", "Russian Ruble"),
        ("USD", "US Dollar"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wallets")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    balance = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.user.username}'s Wallet - {self.currency}"


class Transaction(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    sender = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="transactions_sent"
    )
    recipient = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="transactions_received"
    )

    def save(self, *args, **kwargs):
        if self.sender.id == self.recipient.id:
            logger.error(
                "Попытка перевода самому себе %s -> %s",
                self.sender.id,
                self.recipient.id,
            )
            raise ValidationError("Нельзя переводить самому себе")
        if self.sender.balance < self.amount:
            logger.error("Недостаточно средств на кошельке %s", self.sender.id)
            raise ValidationError("Недостаточно средств на кошельке отправителя")
        if self.sender.currency != self.recipient.currency:
            logger.error(
                "Несовпадение валют кошельков %s -> %s",
                self.sender.id,
                self.recipient.id,
            )
            raise ValidationError("Валюты кошельков должны совпадать")
        with transaction.atomic():
            self.sender.balance -= self.amount
            self.recipient.balance += self.amount
            self.sender.save()
            self.recipient.save()

            super().save(*args, **kwargs)
            logger.info("Транзакция выполнена успешно")

    def __str__(self):
        return f"{self.sender} -> {self.recipient} amount {self.amount} {self.sender.currency}"
