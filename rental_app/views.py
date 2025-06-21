# rental_app/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail

from .models import Item, Rental
from .forms import RentalForm

# 調整商品列表視圖，現在可以根據類別過濾和租金排序
def item_list(request, category=None):
    """
    顯示所有或特定類別商品的列表，並可根據租金排序。
    """
    # 獲取排序參數，預設為 None
    # 'sort_by' 預期值為 'price_asc' (價格升序) 或 'price_desc' (價格降序)
    sort_by = request.GET.get('sort_by')

    if category:
        items = Item.objects.filter(category=category)
        page_title = "所有商品" # 預設標題

        # 修正這裡的邏輯：從 CATEGORY_CHOICES 列表中查找對應的中文名稱
        for choice_value, choice_name in Item.CATEGORY_CHOICES:
            if choice_value == category:
                page_title = choice_name
                break
        page_title = f"{page_title}列表" # 加上「列表」字樣
    else:
        items = Item.objects.all()
        page_title = "所有商品" # 如果沒有指定類別，則顯示「所有商品」

    # --- 新增排序邏輯 ---
    if sort_by == 'price_asc':
        items = items.order_by('price_per_day')
    elif sort_by == 'price_desc':
        items = items.order_by('-price_per_day')
    # 預設排序或沒有指定排序時，保持原來的排序 (或您可以設定一個預設排序)
    # 這裡 'ordering = ['name']' 已經在 models.py 的 Meta 中定義了，會自動應用

    # 將當前的 sort_by 參數也傳遞給模板，以便在模板中顯示當前選擇
    return render(request, 'rental_app/item_list.html', {
        'items': items,
        'page_title': page_title,
        'sort_by': sort_by # 將當前的排序方式傳遞給模板
    })

# 詳情頁面現在處理通用的 Item
def item_detail(request, pk):
    """
    顯示單個商品的詳細資訊及租賃表單。
    """
    item = get_object_or_404(Item, pk=pk)
    form = RentalForm()
    return render(request, 'rental_app/item_detail.html', {'item': item, 'form': form})

# 租賃處理頁面現在處理通用的 Item
def rent_item(request, pk):
    """
    處理商品租賃請求，並在成功後發送 Email 通知管理員和使用者。
    """
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        form = RentalForm(request.POST, instance=Rental(item=item))
        if form.is_valid():
            with transaction.atomic():
                rental = form.save()

                # --- 發送 Email 通知管理員 ---
                admin_subject = f"新商品租賃請求：{item.name} ({item.get_category_display()})"
                admin_message = (
                    f"您好，管理員：\n\n"
                    f"有一筆新的商品租賃請求已提交：\n\n"
                    f"商品名稱: {item.name}\n"
                    f"商品類別: {item.get_category_display()}\n"
                    f"租賃者: {rental.user_name}\n"
                    f"電子郵件: {rental.email}\n"
                    f"起始日期: {rental.start_date.strftime('%Y-%m-%d')}\n"
                    f"結束日期: {rental.end_date.strftime('%Y-%m-%d')}\n"
                    f"總租金: NT${rental.total_price}\n"
                    f"預訂時間: {rental.rented_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"請您登入後台管理系統以確認此租約並更新狀態。\n"
                    f"後台連結: http://127.0.0.1:8000/admin/rental_app/rental/{rental.pk}/change/\n"
                    f"(請注意: 此連結僅在開發環境有效，實際部署需修改為您的域名)"
                )
                admin_from_email = settings.DEFAULT_FROM_EMAIL
                admin_recipient_list = [settings.ADMIN_EMAIL]

                # --- 發送 Email 確認信給使用者 ---
                user_subject = f"您的商品租賃請求已收到 - {item.name}"
                user_message = (
                    f"親愛的 {rental.user_name}：\n\n"
                    f"感謝您在相機租約中心提交的租賃請求！\n\n"
                    f"您的訂單詳情如下：\n"
                    f"商品名稱: {item.name}\n"
                    f"商品類別: {item.get_category_display()}\n"
                    f"起始日期: {rental.start_date.strftime('%Y-%m-%d')}\n"
                    f"結束日期: {rental.end_date.strftime('%Y-%m-%d')}\n"
                    f"預計總租金: NT${rental.total_price}\n"
                    f"訂單狀態: 待確認\n\n"
                    f"我們將盡快審核您的請求，並透過 Email 或電話與您聯繫以確認租約細節。\n\n"
                    f"如有任何疑問，請隨時回覆此郵件或聯繫我們的客服。\n\n"
                    f"祝您拍攝愉快！\n"
                    f"相機租約中心 敬上"
                )
                user_from_email = settings.DEFAULT_FROM_EMAIL
                user_recipient_list = [rental.email]

                try:
                    send_mail(admin_subject, admin_message, admin_from_email, admin_recipient_list, fail_silently=False)
                    print(f"成功發送租賃通知 Email 給管理員 ({settings.ADMIN_EMAIL})")

                    send_mail(user_subject, user_message, user_from_email, user_recipient_list, fail_silently=False)
                    print(f"成功發送租賃確認 Email 給使用者 ({rental.email})")

                except Exception as e:
                    print(f"發送 Email 失敗：{e}")

                return redirect('my_rentals')
        else:
            return render(request, 'rental_app/item_detail.html', {'item': item, 'form': form})
    return redirect('item_detail', pk=pk)

def my_rentals(request):
    """
    顯示所有租賃訂單。
    """
    rentals = Rental.objects.all()
    return render(request, 'rental_app/my_rentals.html', {'rentals': rentals})

def about_us(request):
    """
    顯示關於我們頁面。
    """
    return render(request, 'rental_app/about_us.html')

def contact_us_view(request):
    """
    渲染聯絡我們頁面
    """
    return render(request, 'rental_app/contact_us.html')