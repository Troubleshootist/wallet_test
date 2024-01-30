from django.urls import path

from . import views

urlpatterns = [
    path("create-wallet/", views.CreateWalletView.as_view(), name="create_wallet"),
    path(
        "create-transaction/",
        views.CreateTransactionView.as_view(),
        name="create_transaction",
    ),
]
