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
    # For simplicity, we use a char field for user name.
    # In a real app, this would be a ForeignKey to Django's User model.
    user_name = models.CharField(max_length=100, verbose_name="租賃者姓名", help_text="請輸入您的姓名")
    email = models.EmailField(verbose_name="電子郵件", help_text="請輸入您的電子郵件地址") # 新增 Email 欄位
    start_date = models.DateField(verbose_name="租賃開始日期")
    end_date = models.DateField(verbose_name="租賃結束日期")
    total_price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="總租金")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="租賃狀態")
    rented_at = models.DateTimeField(auto_now_add=True, verbose_name="預訂時間")

    class Meta:
        verbose_name = "租賃訂單"
        verbose_name_plural = "租賃訂單"
        ordering = ['-rented_at'] # 依預訂時間降序排列

    def __str__(self):
        return f"{self.user_name} 租賃 {self.camera.name} ({self.start_date} 至 {self.end_date})"

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
        在保存租賃訂單前計算總價。
        """
        self.calculate_total_price()
        super().save(*args, **kwargs)
