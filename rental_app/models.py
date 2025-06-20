# rental_app/models.py
from django.db import models
from django.utils import timezone
import datetime

class Camera(models.Model):
    """
    相機模型，定義可租賃的相機產品。
    """
    name = models.CharField(max_length=200, verbose_name="相機名稱")
    description = models.TextField(blank=True, verbose_name="描述")
    price_per_day = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="每日租金")
    # Placeholder for image. In a real app, you'd use ImageField and handle uploads.
    # Here, a simple URL for demonstration.
    image_url = models.URLField(blank=True, null=True, verbose_name="圖片URL",
                                help_text="請提供相機圖片的URL")
    is_available = models.BooleanField(default=True, verbose_name="是否可用")

    class Meta:
        verbose_name = "相機"
        verbose_name_plural = "相機"

    def __str__(self):
        return self.name

class Rental(models.Model):
    """
    租賃訂單模型，記錄用戶租賃相機的詳情。
    """
    STATUS_CHOICES = [
        ('pending', '待確認'),
        ('active', '租賃中'),
        ('returned', '已歸還'),
        ('cancelled', '已取消'),
    ]

    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, verbose_name="租賃相機")
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
        if self.start_date and self.end_date and self.camera.price_per_day:
            duration = (self.end_date - self.start_date).days + 1 # 包含首尾兩天
            if duration > 0:
                self.total_price = self.camera.price_per_day * duration
            else:
                self.total_price = 0 # 日期無效或相同
        else:
            self.total_price = 0

    def save(self, *args, **kwargs):
        """
        在保存租賃訂單前計算總價，並在保存後更新相機的可用性。
        """
        original_status = None
        if self.pk: # 如果是現有實例，先獲取原始狀態以便判斷是否發生了狀態變化
            try:
                original_rental = Rental.objects.get(pk=self.pk)
                original_status = original_rental.status
            except Rental.DoesNotExist:
                pass # 如果找不到原始記錄，可能是新建操作，無需比較原始狀態

        self.calculate_total_price() # 計算總價
        is_new_rental = not self.pk # 檢查是否為新租賃訂單

        super().save(*args, **kwargs) # 先保存租賃訂單實例

        camera = self.camera

        # --- 增強：根據租賃訂單的新狀態更新相機的可用性 ---
        # 情況 1: 新建訂單 (預設為 'pending') 或狀態變為 'pending' 或 'active'
        # 在這些情況下，相機應立即設為不可用
        if (is_new_rental and self.status == 'pending') or \
           (self.status == 'pending' and original_status not in ['pending', 'active']) or \
           (self.status == 'active' and original_status not in ['pending', 'active']): # 從非 pending/active 轉為 pending/active
            if camera.is_available: # 僅在相機目前可用時才改變狀態
                camera.is_available = False
                camera.save()
        # 情況 2: 狀態變為 'returned' (已歸還) 或 'cancelled' (已取消)
        elif self.status in ['returned', 'cancelled']:
            # 只有當狀態確實發生變化 (從 pending/active 轉為 returned/cancelled) 才觸發檢查
            if original_status in ['pending', 'active']:
                # 檢查這台相機是否還有其他 'pending' 或 'active' 的租賃訂單
                # 排除當前正在保存的訂單，因為它的狀態已經是 returned/cancelled
                other_ongoing_rentals = Rental.objects.filter(
                    camera=camera,
                    status__in=['pending', 'active']
                ).exclude(pk=self.pk) # 排除當前被修改的租賃訂單

                # 如果沒有其他進行中或待確認的租賃訂單，則將相機設為可用
                if not other_ongoing_rentals.exists():
                    camera.is_available = True
                    camera.save()
