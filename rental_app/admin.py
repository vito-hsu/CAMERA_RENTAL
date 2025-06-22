# rental_app/admin.py
from django.contrib import admin
from .models import Item, Rental

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """
    自定義商品模型在管理介面中的顯示。
    """
    # 確保 'is_recommended' 顯示在管理列表頁面中
    # 新增 is_recommended 到 list_display
    list_display = ('name', 'category', 'price_per_day', 'is_available', 'is_recommended')
    
    # 增加 'is_recommended' 作為篩選器，方便您快速篩選推薦商品
    # 新增 is_recommended 到 list_filter
    list_filter = ('category', 'is_available', 'is_recommended',)
    
    search_fields = ('name', 'description')
    
    # 允許在列表頁面直接編輯 'is_recommended'
    # 新增 is_recommended 到 list_editable
    list_editable = ('price_per_day', 'is_available', 'is_recommended') 
    
    # 或者，如果您不希望在列表頁直接編輯，但希望在商品編輯頁面看到，確保它在 fields 或 fieldsets 中：
    # fields = ('name', 'description', 'price_per_day', 'image_url', 'is_available', 'category', 'is_recommended')

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