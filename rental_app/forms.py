# rental_app/forms.py
from django import forms
from .models import Rental, Item # 從 models 導入 Item 而非 Camera
from django.core.exceptions import ValidationError
from django.forms.widgets import DateInput
from django.utils import timezone # 確保導入 timezone

class RentalForm(forms.ModelForm):
    """
    用於租賃商品的表單。
    """
    class Meta:
        model = Rental
        fields = ['user_name', 'email', 'start_date', 'end_date']
        widgets = {
            'start_date': DateInput(attrs={'type': 'date'}),
            'end_date': DateInput(attrs={'type': 'date'}),
            'user_name': forms.TextInput(attrs={'placeholder': '您的姓名'}),
            'email': forms.EmailInput(attrs={'placeholder': '您的電子郵件地址'}),
        }
        labels = {
            'user_name': '您的姓名',
            'email': '電子郵件',
            'start_date': '開始日期',
            'end_date': '結束日期',
        }

    def clean(self):
        """
        自定義表單驗證，確保日期有效且商品在庫存中可用。
        """
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        # 表單中的 item 實例應該從 view 傳入 (例如 self.instance.item)
        # 由於 RentalForm 預設沒有直接的 item 欄位，我們從 Rental 實例中獲取
        # 在 views.py 中創建 RentalForm 時，我們會將 item 關聯到 instance
        # 因此這裡假設 self.instance.item 是可用的
        item = self.instance.item if self.instance and self.instance.item else None

        if start_date and end_date:
            if start_date < timezone.now().date():
                raise ValidationError("開始日期不能早於今天。")
            if end_date < start_date:
                raise ValidationError("結束日期不能早於開始日期。")

            if item: # 檢查 item 而非 camera
                # 首先檢查 item.is_available 總體狀態
                if not item.is_available:
                     raise ValidationError(f"{item.name} 目前不可用。")

                # 進階庫存檢查：檢查是否有重疊的租賃
                # 假設一個 item 只有一個實體
                overlapping_rentals = Rental.objects.filter(
                    item=item, # 變更為 item
                    start_date__lte=end_date,
                    end_date__gte=start_date,
                ).exclude(status__in=['returned', 'cancelled'])

                if self.instance.pk: # 如果是編輯現有租賃
                    overlapping_rentals = overlapping_rentals.exclude(pk=self.instance.pk)

                if overlapping_rentals.exists():
                    raise ValidationError(f"{item.name} 在您選擇的日期範圍內已被預訂。")

        return cleaned_data
