# rental_app/forms.py

from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from .models import Rental, Item # 確保 Item 模型也被導入
from django.db.models import Q # 確保 Q 有導入

class RentalForm(forms.ModelForm):
    # 手動定義日期欄位，以便於在模板中添加特定屬性 (如 type="date")
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="起始日期"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="結束日期"
    )

    class Meta:
        model = Rental
        fields = ['user_name', 'email', 'phone_number', 'start_date', 'end_date'] # <--- 確保這裡有 'phone_number'
        labels = {
            'user_name': '您的姓名',
            'email': '電子郵件',
            'phone_number': '手機號碼 (選填)',
            'start_date': '起始日期',
            'end_date': '結束日期',
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        item = self.instance.item # 從表單實例獲取商品對象，由 views.py 傳入

        # 檢查日期有效性
        if start_date and end_date:
            if start_date < date.today():
                raise ValidationError("起始日期不能早於今天。", code='past_start_date')
            if end_date < start_date:
                raise ValidationError("結束日期不能早於起始日期。", code='invalid_end_date')

            # 檢查商品是否存在且可用
            if not item:
                raise ValidationError("要租賃的商品不存在。", code='item_not_found')
            # 因為 save 方法會處理 is_available，這裡只檢查初始狀態
            # if not item.is_available: # 這行可以根據需求決定是否保留，如果只想允許租賃 'is_available=True' 的商品則保留
            #     raise ValidationError(f"{item.name} 目前不可租賃。", code='item_not_available')

            # 檢查日期衝突
            # 查找在指定日期範圍內與當前商品有重疊的租賃訂單 (不包括已取消或已歸還的)
            conflicting_rentals = Rental.objects.filter(
                # 將 Q 物件放在所有關鍵字參數之前
                Q(start_date__lte=end_date, end_date__gte=start_date),
                item=item,
                status__in=['pending', 'approved'] # 考慮待確認和已確認的租賃
            ).exclude(pk=self.instance.pk) # 排除掉當前正在編輯的租賃實例（如果有的話，對於新建則無影響）

            if conflicting_rentals.exists():
                raise ValidationError(
                    f"{item.name} 在您選擇的日期範圍 ({start_date} 到 {end_date}) 內已被預訂。請選擇其他日期。",
                    code='date_conflict'
                )

        return cleaned_data