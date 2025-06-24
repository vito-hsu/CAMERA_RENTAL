# rental_app/forms.py

from django import forms
from django.core.exceptions import ValidationError
from datetime import date # 仍然需要導入 date，因為 clean 方法可能仍會處理日期物件
from .models import Rental, Item
from django.db.models import Q

class RentalForm(forms.ModelForm):
    # 手動定義日期欄位
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'id': 'rentalStartDate',
            'class': 'form-control form-control-lg flatpickr-input',
            'placeholder': '請選擇起始日期',
            'autocomplete': 'off'
        }),
        label="起始日期"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'id': 'rentalEndDate',
            'class': 'form-control form-control-lg flatpickr-input',
            'placeholder': '請選擇結束日期',
            'autocomplete': 'off'
        }),
        label="結束日期"
    )

    class Meta:
        model = Rental
        fields = ['user_name', 'email', 'phone_number', 'start_date', 'end_date']
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

        # --- 移除所有日期有效性檢查 ---
        # if start_date and end_date:
        #     if start_date < date.today():
        #         raise ValidationError("起始日期不能早於今天。", code='past_start_date')
        #     if end_date < start_date:
        #         raise ValidationError("結束日期不能早於起始日期。", code='invalid_end_date')
        # ----------------------------

        # 檢查商品是否存在 (這個邏輯與日期選擇無關，可以保留)
        if not item:
            raise ValidationError("要租賃的商品不存在。", code='item_not_found')
        
        # 檢查日期衝突 (這個邏輯與日期選擇無關，是資料庫層面的邏輯，可以保留)
        if start_date and end_date: # 只有當兩個日期都存在時才檢查衝突
            conflicting_rentals = Rental.objects.filter(
                Q(start_date__lte=end_date, end_date__gte=start_date),
                item=item,
                status__in=['pending', 'approved']
            ).exclude(pk=self.instance.pk)

            if conflicting_rentals.exists():
                raise ValidationError(
                    f"{item.name} 在您選擇的日期範圍 ({start_date} 到 {end_date}) 內已被預訂。請選擇其他日期。",
                    code='date_conflict'
                )

        return cleaned_data