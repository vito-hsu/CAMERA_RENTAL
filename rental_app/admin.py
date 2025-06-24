# rental_app/admin.py
from django.contrib import admin
from .models import Item, Rental

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """
    自定義商品模型在管理介面中的顯示。
    """
    # 確保 'deposit' 顯示在管理列表頁面中
    list_display = ('name', 'category', 'price_per_day', 'deposit', 'is_available', 'is_recommended') # <--- 添加 'deposit'
    
    # 增加 'is_recommended' 作為篩選器，方便您快速篩選推薦商品
    list_filter = ('category', 'is_available', 'is_recommended',)
    
    search_fields = ('name', 'description')
    
    # 允許在列表頁面直接編輯 'price_per_day', 'is_available', 'is_recommended' 和 'deposit'
    list_editable = ('price_per_day', 'deposit', 'is_available', 'is_recommended') # <--- 添加 'deposit'
    
    # 或者，如果您不希望在列表頁直接編輯，但希望在商品編輯頁面看到，確保它在 fields 或 fieldsets 中：
    # fields = ('name', 'description', 'price_per_day', 'deposit', 'image_url', 'is_available', 'category', 'is_recommended') # <--- 這裡如果使用，也要添加 'deposit'

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    """
    自定義租賃訂單模型在管理介面中的顯示。
    """
    list_display = ('item', 'user_name', 'email', 'start_date', 'end_date', 'total_price', 'status', 'rented_at')
    list_filter = ('status', 'start_date', 'end_date', 'item__category')
    search_fields = ('user_name', 'email', 'item__name')
    date_hierarchy = 'rented_at'
    readonly_fields = ('total_price', 'rented_at')