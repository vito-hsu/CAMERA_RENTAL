# rental_app/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q 
# 假設您有用戶認證，並希望 my_rentals 需要登入
# from django.contrib.auth.decorators import login_required 

# 確保這裡的模型名稱與 models.py 中的定義一致。
# 根據您現在的代碼，假設是 Item 和 Rental。
from .models import Item, Rental 
from .forms import RentalForm

def rental_terms(request):
    page_title = "租賃規章"
    return render(request, 'rental_app/rental_terms.html', {'page_title': page_title})


def homepage(request):
    """
    顯示網站首頁，現在會顯示後台設定的推薦商品。
    """
    recommended_items = Item.objects.filter(
        is_recommended=True, 
        is_available=True 
    )[:8] 

    return render(request, 'rental_app/homepage.html', {'items': recommended_items})

# 調整商品列表視圖，現在可以根據類別過濾和租金排序
def item_list(request, category=None): # <--- 這裡改為 category=None
    """
    顯示所有或特定類別商品的列表，並可根據租金排序。
    """
    sort_by = request.GET.get('sort_by')
    
    items = Item.objects.all() # 初始查詢集，默認為所有商品
    page_title = "所有商品" # 預設標題

    if category:
        items = items.filter(category=category)
        # 從 CATEGORY_CHOICES 列表中查找對應的中文名稱
        for choice_value, choice_name in Item.CATEGORY_CHOICES:
            if choice_value == category:
                page_title = choice_name
                break
        page_title = f"{page_title}列表" 
    
    # --- 排序邏輯 ---
    if sort_by == 'price_asc':
        items = items.order_by('price_per_day')
    elif sort_by == 'price_desc':
        items = items.order_by('-price_per_day')
    else:
        # 如果沒有指定排序或排序參數無效，則使用模型預設排序（如果 Meta 中定義了）
        # 或者手動設定一個預設排序，例如按名稱升序
        items = items.order_by('name') 

    return render(request, 'rental_app/item_list.html', {
        'items': items,
        'page_title': page_title,
        'sort_by': sort_by 
    })

def item_detail(request, pk):
    """
    顯示單個商品的詳細資訊及租賃表單。
    """
    item = get_object_or_404(Item, pk=pk)
    form = RentalForm()
    return render(request, 'rental_app/item_detail.html', {'item': item, 'form': form})

def rent_item(request, pk):
    """
    處理商品租賃請求，並在成功後發送 Email 通知管理員和使用者。
    """
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        # 注意這裡的 instance=Rental(item=item)，如果 RentalForm 不包含 item 字段，
        # 且 item 字段是必填的，則可能需要在這裡處理好。
        # 更好的做法通常是在 clean() 方法中賦值，或者在 save(commit=False) 後賦值。
        # 假設 RentalForm 會處理好 item 關聯。
        form = RentalForm(request.POST, instance=Rental(item=item)) 
        if form.is_valid():
            try:
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
                        f"總租金: NT${rental.total_price}\n" # 確保 total_price 已經在表單 clean 或模型 save 方法中計算
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

                    send_mail(admin_subject, admin_message, admin_from_email, admin_recipient_list, fail_silently=False)
                    print(f"成功發送租賃通知 Email 給管理員 ({settings.ADMIN_EMAIL})")

                    send_mail(user_subject, user_message, user_from_email, user_recipient_list, fail_silently=False)
                    print(f"成功發送租賃確認 Email 給使用者 ({rental.email})")

            except Exception as e:
                print(f"發送 Email 失敗：{e}")
                # 在這裡可以添加錯誤訊息給用戶
                return render(request, 'rental_app/item_detail.html', {'item': item, 'form': form, 'error_message': '租賃請求失敗，請稍後再試。'})

            return redirect('my_rentals') # 假設成功後跳轉到我的租賃
        else:
            # 表單無效時，重新渲染詳情頁面並顯示錯誤
            return render(request, 'rental_app/item_detail.html', {'item': item, 'form': form})
    return redirect('item_detail', pk=pk) # 如果是 GET 請求到 /rent/，重定向回詳情頁

# @login_required # 如果希望只有登入用戶能看自己的租賃，請取消註解
def my_rentals(request):
    """
    顯示所有租賃訂單。
    如果取消 login_required 註解，這裡應該是：
    rentals = Rental.objects.filter(user=request.user).order_by('-rented_at')
    """
    rentals = Rental.objects.all() # 目前是顯示所有租賃
    return render(request, 'rental_app/my_rentals.html', {'rentals': rentals})

def about_us(request):
    """
    顯示關於我們頁面。
    """
    return render(request, 'rental_app/about_us.html')

def contact_us_view(request):
    """
    渲染聯絡我們頁面。
    """
    return render(request, 'rental_app/contact_us.html')

def product_search_view(request):
    """
    處理商品關鍵字搜尋請求。
    此函數會搜尋所有商品 (無論是否可用)，並在模板中顯示其可用狀態。
    """
    query = request.GET.get('q', '') 

    items = Item.objects.all() # 這裡保持 Item.objects.all() 或不包含 is_available=True 的篩選

    if query:
        items = items.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).distinct() 

    context = {
        'query': query,
        'items': items,
        'page_title': f"搜尋結果：'{query}'" if query else "所有商品",
    }
    return render(request, 'rental_app/product_search_results.html', context)