# rental_app/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.contrib import messages
import logging
from .models import Rental, Item # <-- 在這裡添加或確保有 Item 的導入！
from .forms import RentalForm 

logger = logging.getLogger(__name__)


def rental_terms(request):
    page_title = "租賃規章"
    return render(request, 'rental_app/rental_terms.html', {'page_title': page_title})


def homepage(request):
    recommended_items = Item.objects.filter(
        is_recommended=True,
        is_available=True
    )[:8]

    return render(request, 'rental_app/homepage.html', {'items': recommended_items})


def item_list(request, category=None):
    sort_by = request.GET.get('sort_by')

    items = Item.objects.all()
    page_title = "所有商品"

    if category:
        items = items.filter(category=category)
        for choice_value, choice_name in Item.CATEGORY_CHOICES:
            if choice_value == category:
                page_title = choice_name
                break
        page_title = f"{page_title}列表"

    if sort_by == 'price_asc':
        items = items.order_by('price_per_day')
    elif sort_by == 'price_desc':
        items = items.order_by('-price_per_day')
    else:
        items = items.order_by('name')

    return render(request, 'rental_app/item_list.html', {
        'items': items,
        'page_title': page_title,
        'sort_by': sort_by
    })


def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    form = RentalForm()
    return render(request, 'rental_app/item_detail.html', {'item': item, 'form': form})


def rent_item(request, pk):
    logger.info(f"rent_item view 被呼叫，商品 ID: {pk}")
    item = get_object_or_404(Item, pk=pk)

    if request.method == 'POST':
        rental_instance = Rental(item=item)
        form = RentalForm(request.POST, instance=rental_instance)

        if form.is_valid():
            logger.info("表單驗證成功，嘗試保存租賃並發送 Email。")
            try:
                with transaction.atomic():
                    rental = form.save() # save 方法會自動計算 total_price
                    logger.info(f"租賃實例已保存: Rental ID {rental.pk}")

                    # --- 發送 Email 通知管理員 ---
                    admin_subject = f"新商品租賃請求：{item.name} ({item.get_category_display()})"
                    admin_message = (
                        f"您好，管理員：\n\n"
                        f"有一筆新的商品租賃請求已提交：\n\n"
                        f"商品名稱: {item.name}\n"
                        f"商品類別: {item.get_category_display()}\n"
                        f"租賃者: {rental.user_name}\n"
                        f"電子郵件: {rental.email}\n"
                        f"手機號碼: {rental.phone_number if rental.phone_number else '未提供'}\n" # <-- 這裡直接使用 rental.phone_number
                        f"起始日期: {rental.start_date.strftime('%Y-%m-%d')}\n"
                        f"結束日期: {rental.end_date.strftime('%Y-%m-%d')}\n"
                        f"預計總租金: NT${rental.total_price}\n" # <-- 直接使用 rental.total_price (模型中已存在)
                        f"預訂時間: {rental.rented_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                        f"請您登入後台管理系統以確認此租約並更新狀態。\n"
                        f"後台連結: {request.build_absolute_uri(reverse('admin:rental_app_rental_change', args=[rental.pk]))}\n"
                        f"(請注意: 此連結的域名部分將根據您的實際部署環境自動生成)"
                    )
                    admin_from_email = settings.DEFAULT_FROM_EMAIL
                    admin_recipient_list = [settings.ADMIN_EMAIL]
                    logger.info(f"管理員 Email 接收者: {admin_recipient_list}")

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
                        f"預計總租金: NT${rental.total_price}\n" # <-- 直接使用 rental.total_price
                        f"訂單狀態: 待確認\n\n"
                        f"我們將盡快審核您的請求，並透過 Email 或電話與您聯繫以確認租約細節。\n\n"
                        f"如有任何疑問，請隨時回覆此郵件或聯繫我們的客服。\n\n"
                        f"祝您拍攝愉快！\n"
                        f"相機租約中心 敬上"
                    )
                    user_from_email = settings.DEFAULT_FROM_EMAIL
                    user_recipient_list = [rental.email]
                    logger.info(f"使用者 Email 接收者: {user_recipient_list}")

                    try:
                        logger.info("嘗試發送管理員 Email...")
                        send_mail(admin_subject, admin_message, admin_from_email, admin_recipient_list, fail_silently=False)
                        logger.info(f"成功發送租賃通知 Email 給管理員 ({settings.ADMIN_EMAIL})")
                    except Exception as e:
                        logger.error(f"發送管理員 Email 失敗：{e}", exc_info=True)
                        messages.error(request, "管理員 Email 通知發送失敗，但租賃已記錄。")

                    try:
                        logger.info("嘗試發送使用者 Email...")
                        send_mail(user_subject, user_message, user_from_email, user_recipient_list, fail_silently=False)
                        logger.info(f"成功發送租賃確認 Email 給使用者 ({rental.email})")
                    except Exception as e:
                        logger.error(f"發送使用者 Email 失敗：{e}", exc_info=True)
                        messages.error(request, "使用者 Email 確認信發送失敗。")

                messages.success(request, f"您已成功預訂 {item.name} 從 {rental.start_date} 到 {rental.end_date}。我們已發送確認信到您的郵箱。")
                return redirect('my_rentals')
            except ValidationError as e:
                logger.warning(f"表單驗證錯誤: {e.message}")
                messages.error(request, e.message)
                return render(request, 'rental_app/item_detail.html', {'item': item, 'form': form})
            except Exception as e:
                logger.exception(f"處理租賃請求時發生意外錯誤: {e}")
                messages.error(request, f"租賃請求失敗，發生系統錯誤：{e}")
                return render(request, 'rental_app/item_detail.html', {'item': item, 'form': form})
        else:
            logger.info("表單驗證失敗。")
            messages.error(request, "請檢查您的租賃信息，有錯誤發生。")
            return render(request, 'rental_app/item_detail.html', {'item': item, 'form': form})
    logger.info("接收到 GET 請求，重定向回商品詳情頁。")
    return redirect('item_detail', pk=pk)


def my_rentals(request):
    rentals = Rental.objects.all().order_by('-rented_at')
    return render(request, 'rental_app/my_rentals.html', {'rentals': rentals})


def about_us(request):
    return render(request, 'rental_app/about_us.html')


def contact_us_view(request):
    return render(request, 'rental_app/contact_us.html')


def product_search_view(request):
    query = request.GET.get('q', '')

    items = Item.objects.all()

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