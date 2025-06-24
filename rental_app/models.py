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
        ('other', '其他'), # <--- Changed back to 'other'
    ]

    name = models.CharField(max_length=200, verbose_name="品項名稱")
    description = models.TextField(blank=True, verbose_name="描述")
    price_per_day = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="每日租金")
    # --- 新增 deposit 字段，預設值為 0 ---
    deposit = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="商品押金")
    # ------------------------------------
    image_url = models.URLField(blank=True, null=True, verbose_name="圖片URL",
                                  help_text="請提供品項圖片的URL")
    is_available = models.BooleanField(default=True, verbose_name="是否可用")
    category = models.CharField(
        max_length=50, # <--- This length is fine for the new choices too
        choices=CATEGORY_CHOICES,
        default='camera',
        verbose_name="品項類別"
    )
    is_recommended = models.BooleanField(default=False, verbose_name="推薦商品 (顯示於首頁)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="創建時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")


    class Meta:
        verbose_name = "商品"
        verbose_name_plural = "商品"
        ordering = ['name']

    def __str__(self):
        return f"[{self.get_category_display()}] {self.name}"

# You might still have your Rental model here
class Rental(models.Model):
    """
    租賃訂單模型，記錄用戶租賃商品的詳情。
    現在連結到通用的 Item 模型。
    """
    STATUS_CHOICES = [
        ('pending', '待確認'),
        ('approved', '已確認'),
        ('returned', '已歸還'),
        ('cancelled', '已取消'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='rentals', verbose_name="租賃商品")
    user_name = models.CharField(max_length=100, verbose_name="租賃者姓名", help_text="請輸入您的姓名")
    email = models.EmailField(verbose_name="電子郵件", help_text="請輸入您的電子郵件地址")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="手機號碼")
    start_date = models.DateField(verbose_name="租賃開始日期")
    end_date = models.DateField(verbose_name="租賃結束日期")
    total_price = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True, verbose_name="總租金")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="租賃狀態")
    rented_at = models.DateTimeField(auto_now_add=True, verbose_name="預訂時間")

    class Meta:
        verbose_name = "租賃訂單"
        verbose_name_plural = "租賃訂單"
        ordering = ['-rented_at']

    def calculate_total_price(self):
        """
        計算總租金 (不含押金)。
        """
        if self.start_date and self.end_date and self.item.price_per_day is not None:
            duration = (self.end_date - self.start_date).days + 1
            if duration > 0:
                self.total_price = self.item.price_per_day * duration
            else:
                self.total_price = 0
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
        if (is_new_rental and self.status == 'pending') or \
           (self.status == 'pending' and original_status not in ['pending', 'approved']) or \
           (self.status == 'approved' and original_status not in ['pending', 'approved']):
            if item.is_available:
                item.is_available = False
                item.save()
        elif self.status in ['returned', 'cancelled']:
            if original_status in ['pending', 'approved']:
                other_ongoing_rentals = Rental.objects.filter(
                    item=item,
                    status__in=['pending', 'approved']
                ).exclude(pk=self.pk)

                if not other_ongoing_rentals.exists():
                    item.is_available = True
                    item.save()

    def __str__(self):
        return f"{self.user_name} - {self.item.name} ({self.start_date} to {self.end_date})"