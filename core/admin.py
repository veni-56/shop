from django.contrib import admin
from .models import *


admin.site.register(UserProfile)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount', 'active']
    search_fields = ['code']
    list_filter = ['active']


admin.site.register(Category)
admin.site.register(Product)