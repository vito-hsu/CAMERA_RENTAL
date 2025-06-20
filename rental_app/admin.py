# rental_app/admin.py
from django.contrib import admin
from .models import Camera, Rental

@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    """
    自定義相機模型在管理介面中的顯示。
    """
    list_display = ('name', 'price_per_day', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('name', 'description')

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    """
    自定義租賃訂單模型在管理介面中的顯示。
    """
    list_display = ('camera', 'user_name', 'email', 'start_date', 'end_date', 'total_price', 'status', 'rented_at') # 新增 'email'
    list_filter = ('status', 'start_date', 'end_date', 'camera')
    search_fields = ('user_name', 'email') # 可以在 Admin 中透過 Email 搜尋
    date_hierarchy = 'rented_at'
    # 設置預設只讀字段，避免管理員在後台直接修改某些字段
    readonly_fields = ('total_price', 'rented_at')
