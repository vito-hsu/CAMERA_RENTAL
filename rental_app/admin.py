# rental_app/admin.py
from django.contrib import admin
from .models import Item, Rental # 從 models 導入 Item 而非 Camera

@admin.register(Item) # 註冊 Item 模型
class ItemAdmin(admin.ModelAdmin):
    """
    自定義商品模型在管理介面中的顯示。
    """
    list_display = ('name', 'category', 'price_per_day', 'is_available') # 新增 category
    list_filter = ('category', 'is_available',) # 可以按類別過濾
    search_fields = ('name', 'description')

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    """
    自定義租賃訂單模型在管理介面中的顯示。
    """
    list_display = ('item', 'user_name', 'email', 'start_date', 'end_date', 'total_price', 'status', 'rented_at') # 這裡的 item 會自動顯示 Item 的 __str__ 方法
    list_filter = ('status', 'start_date', 'end_date', 'item__category') # 可以按商品類別過濾租賃訂單
    search_fields = ('user_name', 'email', 'item__name') # 可以搜尋商品名稱
    date_hierarchy = 'rented_at'
    readonly_fields = ('total_price', 'rented_at')
