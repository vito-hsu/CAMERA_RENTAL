# rental_app/forms.py
from django import forms
from .models import Rental, Camera
from django.core.exceptions import ValidationError
from django.forms.widgets import DateInput
from django.utils import timezone

class RentalForm(forms.ModelForm):
    """
    用於租賃相機的表單。
    """
    class Meta:
        model = Rental
        fields = ['user_name', 'email', 'start_date', 'end_date'] # 新增 'email'
        widgets = {
            'start_date': DateInput(attrs={'type': 'date'}),
            'end_date': DateInput(attrs={'type': 'date'}),
            'user_name': forms.TextInput(attrs={'placeholder': '您的姓名'}),
            'email': forms.EmailInput(attrs={'placeholder': '您的電子郵件地址'}), # 新增 Email 輸入框
        }
        labels = {
            'user_name': '您的姓名',
            'email': '電子郵件', # 新增 Email 標籤
            'start_date': '開始日期',
            'end_date': '結束日期',
        }

    def clean(self):
        """
        自定義表單驗證，確保日期有效且相機在庫存中可用。
        """
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        camera = self.instance.camera if self.instance.pk else None # 僅在更新時有instance

        if start_date and end_date:
            if start_date < timezone.now().date():
                raise ValidationError("開始日期不能早於今天。")
            if end_date < start_date:
                raise ValidationError("結束日期不能早於開始日期。")

            if camera:
                # 檢查相機在選定日期範圍內是否可用
                # 這個邏輯需要更嚴謹，真正實作會檢查該相機在日期範圍內是否有重疊租賃
                # 在這個簡單範例中，我們只檢查 camera.is_available
                if not camera.is_available:
                     raise ValidationError(f"{camera.name} 目前不可用。")

                # 進階庫存檢查（簡化）：檢查是否有重疊的租賃
                # 假設一個相機只有一個實體
                overlapping_rentals = Rental.objects.filter(
                    camera=camera,
                    start_date__lte=end_date,
                    end_date__gte=start_date,
                ).exclude(status__in=['returned', 'cancelled']) # 排除已歸還或取消的訂單

                if self.instance.pk: # 如果是編輯現有租賃
                    overlapping_rentals = overlapping_rentals.exclude(pk=self.instance.pk)

                if overlapping_rentals.exists():
                    raise ValidationError(f"{camera.name} 在您選擇的日期範圍內已被預訂。")

        return cleaned_data
