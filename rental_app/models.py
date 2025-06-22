# rental_app/models.py
from django.db import models
from django.utils import timezone
import datetime

# 將 Camera 模型變更為 Item 模型
class Item(models.Model):
    """
    通用商品模型，定義可租賃的任何品項，如相機、鏡頭、其他配件。
    """
    CATEGORY_CHOICES = [
        ('camera', '相機'),
        ('lens', '鏡頭'),
        ('other', '其他品項'),
    ]

    name = models.CharField(max_length=200, verbose_name="品項名稱")
    description = models.TextField(blank=True, verbose_name="描述")
    price_per_day = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="每日租金")
    image_url = models.URLField(blank=True, null=True, verbose_name="圖片URL",
                                 help_text="請提供品項圖片的URL")
    is_available = models.BooleanField(default=True, verbose_name="是否可用")
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='camera',
        verbose_name="品項類別"
    )
    # *** 請在上面這行之後新增以下這行 ***
    is_recommended = models.BooleanField(default=False, verbose_name="推薦商品 (顯示於首頁)")
    # *** 新增完成 ***


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
        ('active', '租賃中'),
        ('returned', '已歸還'),
        ('cancelled', '已取消'),
    ]

    # 將外鍵從 Camera 變更為 Item
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="租賃商品")
    user_name = models.CharField(max_length=100, verbose_name="租賃者姓名", help_text="請輸入您的姓名")
    email = models.EmailField(verbose_name="電子郵件", help_text="請輸入您的電子郵件地址")
    start_date = models.DateField(verbose_name="租賃開始日期")
    end_date = models.DateField(verbose_name="租賃結束日期")
    total_price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="總租金")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="租賃狀態")
    rented_at = models.DateTimeField(auto_now_add=True, verbose_name="預訂時間")

    class Meta:
        verbose_name = "租賃訂單"
        verbose_name_plural = "租賃訂單"
        ordering = ['-rented_at'] # 依預訂時間降序排列

    def calculate_total_price(self):
        """
        計算總租金。
        """
        if self.start_date and self.end_date and self.item.price_per_day: # 修改為 item.price_per_day
            duration = (self.end_date - self.start_date).days + 1 # 包含首尾兩天
            if duration > 0:
                self.total_price = self.item.price_per_day * duration # 修改為 item.price_per_day
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

        self.calculate_total_price()
        is_new_rental = not self.pk

        super().save(*args, **kwargs) # 先保存租賃訂單實例

        item = self.item # 變更為 item

        # --- 根據租賃訂單的新狀態更新商品的可用性 ---
        # 情況 1: 新建訂單 (預設為 'pending') 或狀態變為 'pending' 或 'active'
        # 在這些情況下，商品應立即設為不可用
        if (is_new_rental and self.status == 'pending') or \
           (self.status == 'pending' and original_status not in ['pending', 'active']) or \
           (self.status == 'active' and original_status not in ['pending', 'active']):
            if item.is_available: # 僅在商品目前可用時才改變狀態
                item.is_available = False
                item.save()
        # 情況 2: 狀態變為 'returned' (已歸還) 或 'cancelled' (已取消)
        elif self.status in ['returned', 'cancelled']:
            if original_status in ['pending', 'active']:
                # 檢查這台商品是否還有其他 'pending' 或 'active' 的租賃訂單
                other_ongoing_rentals = Rental.objects.filter(
                    item=item, # 變更為 item
                    status__in=['pending', 'active']
                ).exclude(pk=self.pk)

                # 如果沒有其他進行中或待確認的租賃訂單，則將商品設為可用
                if not other_ongoing_rentals.exists():
                    item.is_available = True
                    item.save()
