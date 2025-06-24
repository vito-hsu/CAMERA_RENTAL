# rental_app/models.py
from django.db import models
from django.utils import timezone
import datetime # 確保 datetime 有被導入

# 將 Camera 模型變更為 Item 模型
class Item(models.Model):
    """
    通用商品模型，定義可租賃的任何品項，如相機、鏡頭、其他配件。
    """
    CATEGORY_CHOICES = [
        ('camera', '相機'),
        ('lens', '鏡頭'),
        ('accessory', '配件'), # <--- 修正或新增：將 'other' 改為 'accessory' 或其他更具體的
        ('drone', '空拍機'),   # <--- 新增
        ('lighting', '燈光設備'), # <--- 新增
    ]

    name = models.CharField(max_length=200, verbose_name="品項名稱")
    description = models.TextField(blank=True, verbose_name="描述")
    price_per_day = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="每日租金") # <--- 將 decimal_places 改為 0，max_digits 擴大
    image_url = models.URLField(blank=True, null=True, verbose_name="圖片URL",
                                 help_text="請提供品項圖片的URL")
    is_available = models.BooleanField(default=True, verbose_name="是否可用")
    category = models.CharField(
        max_length=50, # <--- 擴大長度以應對新增的類別
        choices=CATEGORY_CHOICES,
        default='camera',
        verbose_name="品項類別"
    )
    is_recommended = models.BooleanField(default=False, verbose_name="推薦商品 (顯示於首頁)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="創建時間") # <--- 新增
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")   # <--- 新增


    class Meta:
        verbose_name = "商品"
        verbose_name_plural = "商品"
        ordering = ['name']

    def __str__(self):
        return f"[{self.get_category_display()}] {self.name}"
    
class Rental(models.Model):
    """
    租賃訂單模型，記錄用戶租賃商品的詳情。
    現在連結到通用的 Item 模型。
    """
    STATUS_CHOICES = [
        ('pending', '待確認'),
        ('approved', '已確認'), # <--- 將 'active' 更名為 'approved'，更貼合租賃流程
        ('returned', '已歸還'),
        ('cancelled', '已取消'),
    ]

    # 將外鍵從 Camera 變更為 Item
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='rentals', verbose_name="租賃商品") # <--- 添加 related_name
    user_name = models.CharField(max_length=100, verbose_name="租賃者姓名", help_text="請輸入您的姓名")
    email = models.EmailField(verbose_name="電子郵件", help_text="請輸入您的電子郵件地址")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="手機號碼") # <--- 在這裡新增此行！
    start_date = models.DateField(verbose_name="租賃開始日期")
    end_date = models.DateField(verbose_name="租賃結束日期")
    total_price = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True, verbose_name="總租金") # <--- 將 decimal_places 改為 0，max_digits 擴大
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="租賃狀態") # <--- 將 max_length 縮小為 10
    rented_at = models.DateTimeField(auto_now_add=True, verbose_name="預訂時間")

    class Meta:
        verbose_name = "租賃訂單"
        verbose_name_plural = "租賃訂單"
        ordering = ['-rented_at'] # 依預訂時間降序排列

    def calculate_total_price(self):
        """
        計算總租金。
        """
        if self.start_date and self.end_date and self.item.price_per_day is not None: # 確保 price_per_day 不是 None
            duration = (self.end_date - self.start_date).days + 1 # 包含首尾兩天
            if duration > 0:
                self.total_price = self.item.price_per_day * duration
            else:
                self.total_price = 0 # 日期無效或相同
        else:
            self.total_price = 0

    def save(self, *args, **kwargs):
        """
        在保存租賃訂單前計算總價，並在保存後更新商品的可用性。
        """
        original_status = None
        if self.pk:
            try:
                original_rental = Rental.objects.get(pk=self.pk)
                original_status = original_rental.status
            except Rental.DoesNotExist:
                pass

        self.calculate_total_price() # 在保存前計算總價
        is_new_rental = not self.pk

        super().save(*args, **kwargs) # 先保存租賃訂單實例

        item = self.item

        # --- 根據租賃訂單的新狀態更新商品的可用性 ---
        # 情況 1: 新建訂單 (預設為 'pending') 或狀態變為 'pending' 或 'approved'
        # 在這些情況下，商品應立即設為不可用
        if (is_new_rental and self.status == 'pending') or \
           (self.status == 'pending' and original_status not in ['pending', 'approved']) or \
           (self.status == 'approved' and original_status not in ['pending', 'approved']): # <--- 'active' 改為 'approved'
            if item.is_available: # 僅在商品目前可用時才改變狀態
                item.is_available = False
                item.save()
        # 情況 2: 狀態變為 'returned' (已歸還) 或 'cancelled' (已取消)
        elif self.status in ['returned', 'cancelled']:
            if original_status in ['pending', 'approved']: # <--- 'active' 改為 'approved'
                # 檢查這台商品是否還有其他 'pending' 或 'approved' 的租賃訂單
                other_ongoing_rentals = Rental.objects.filter(
                    item=item,
                    status__in=['pending', 'approved'] # <--- 'active' 改為 'approved'
                ).exclude(pk=self.pk)

                # 如果沒有其他進行中或待確認的租賃訂單，則將商品設為可用
                if not other_ongoing_rentals.exists():
                    item.is_available = True
                    item.save()