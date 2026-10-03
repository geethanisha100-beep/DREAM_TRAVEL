from django.contrib import admin
from .models import *
for m in (Destination, Package, Vehicle, Hotel, RoomType, Feedback, Wishlist, Profile):
    admin.site.register(m)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "kind", "item_name", "total", "status", "contact", "created")
    list_filter = ("kind", "status")
    search_fields = ("name", "contact", "item_name")

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("txn_id", "booking", "method", "amount", "email", "phone", "paid_at")
