import logging

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .forms import TransactionCreationForm, WalletCreationForm
from .models import Transaction, Wallet

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class CreateWalletView(View):
    def post(self, request, *args, **kwargs):
        form = WalletCreationForm(request.POST)

        if form.is_valid():
            user_id = form.cleaned_data["user_id"]
            user = User.objects.get(pk=user_id)

            wallet = form.save(commit=False)
            wallet.user = user
            wallet.save()
            logger.info("Кошелек id: %d создан", wallet.id)
            return JsonResponse(
                {
                    "id": wallet.id,
                    "user": wallet.user.username,
                    "currency": wallet.currency,
                    "balance": wallet.balance,
                },
                status=201,
            )
        else:
            return JsonResponse({"errors": form.errors}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class CreateTransactionView(View):
    def post(self, request, *args, **kwargs):
        form = TransactionCreationForm(request.POST)
        if form.is_valid():
            sender_id = form.cleaned_data["sender_id"]
            recipient_id = form.cleaned_data["recipient_id"]
            amount = form.cleaned_data["amount"]

            try:
                sender_wallet = Wallet.objects.get(pk=sender_id)
                recipient_wallet = Wallet.objects.get(pk=recipient_id)
            except Wallet.DoesNotExist:
                logger.error("Ошибка валидации. msg:", form.errors)
                return JsonResponse(
                    {"error": "Один из кошельков не существует"}, status=400
                )

            try:
                Transaction.objects.create(
                    sender=sender_wallet, recipient=recipient_wallet, amount=amount
                )
                return JsonResponse(
                    {"success": "Транзакция успешно создана"}, status=201
                )
            except ValidationError as e:
                logger.error("Ошибка валидации. msg:", form.errors)
                return JsonResponse({"error": str(e)}, status=400)
        else:
            logger.error("Ошибка валидации. msg:", form.errors)
            return JsonResponse({"error": form.errors}, status=400)
