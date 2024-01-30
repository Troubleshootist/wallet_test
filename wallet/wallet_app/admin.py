from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.html import format_html

from .models import Transaction, Wallet


class SendTransactionInline(admin.TabularInline):
    model = Transaction
    verbose_name = "Sent Transaction"
    fk_name = "sender"
    extra = 0
    readonly_fields = ("amount", "sender")


class ReceivedTransactionInline(admin.TabularInline):
    model = Transaction
    verbose_name = "Received Transaction"
    fk_name = "recipient"
    extra = 0
    readonly_fields = ("amount", "sender")


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    inlines = [SendTransactionInline, ReceivedTransactionInline]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["amount"]


class WalletInline(admin.TabularInline):
    model = Wallet
    fields = ("currency", "balance", "view_wallet_link")
    readonly_fields = ("currency", "balance", "view_wallet_link")
    extra = 0

    def view_wallet_link(self, instance):
        if instance.pk:
            url = reverse("admin:wallet_app_wallet_change", args=[instance.pk])
            return format_html("<a href='{}'>View Wallet</a>", url)
        return "-"

    view_wallet_link.short_description = "Wallet"


admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "email", "first_name", "last_name"]
    inlines = [WalletInline]
