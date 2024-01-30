import logging

from django import forms
from django.contrib.auth.models import User

from .models import Transaction, Wallet

logger = logging.getLogger(__name__)


class WalletCreationForm(forms.ModelForm):
    user_id = forms.IntegerField()

    def clean_user_id(self):
        user_id = self.cleaned_data["user_id"]
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            logger.error("Попытка создать кошелек у несуществующего пользователя")
            raise forms.ValidationError(
                "Пользователь с данным идентификатором не существует"
            )
        return user.id

    class Meta:
        model = Wallet
        fields = ["user_id", "currency", "balance"]


class TransactionCreationForm(forms.ModelForm):
    sender_id = forms.IntegerField()
    recipient_id = forms.IntegerField()
    amount = forms.DecimalField()

    def clean_wallet_id(self, wallet_id, field_name):
        try:
            wallet = Wallet.objects.get(pk=wallet_id)
            return wallet.id
        except Wallet.DoesNotExist:
            msg = f"Кошелек с идентификатором {wallet_id} не существует"
            logger.error(msg)
            raise forms.ValidationError(msg)

    def clean_sender_id(self):
        sender_id = self.cleaned_data.get("sender_id")
        return self.clean_wallet_id(sender_id, "sender_id")

    def clean_recipient_id(self):
        recipient_id = self.cleaned_data.get("recipient_id")
        return self.clean_wallet_id(recipient_id, "recipient_id")

    class Meta:
        model = Transaction
        fields = ["sender_id", "recipient_id", "amount"]
