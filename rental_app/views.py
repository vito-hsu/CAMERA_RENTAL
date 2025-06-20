# rental_app/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.conf import settings # 導入 settings 模組來讀取 Email 配置
from django.core.mail import send_mail, EmailMultiAlternatives # 導入發送郵件的函數，包括多種內容類型

from .models import Camera, Rental
from .forms import RentalForm

def camera_list(request):
    """
    顯示所有相機的列表。
    """
    cameras = Camera.objects.all()
    return render(request, 'rental_app/camera_list.html', {'cameras': cameras})

def camera_detail(request, pk):
    """
    顯示單個相機的詳細資訊及租賃表單。
    """
    camera = get_object_or_404(Camera, pk=pk)
    form = RentalForm() # 顯示空白租賃表單
    return render(request, 'rental_app/camera_detail.html', {'camera': camera, 'form': form})

def rent_camera(request, pk):
    """
    處理相機租賃請求，並在成功後發送 Email 通知管理員和使用者。
    """
    camera = get_object_or_404(Camera, pk=pk)
    if request.method == 'POST':
        form = RentalForm(request.POST)
        if form.is_valid():
            with transaction.atomic(): # 確保資料一致性
                rental = form.save(commit=False)
                rental.camera = camera
                rental.status = 'pending' # 預設為待確認
                rental.save()

                # --- 發送 Email 通知管理員 ---
                admin_subject = f"新相機租賃請求：{camera.name}"
                admin_message = (
                    f"您好，管理員：\n\n"
                    f"有一筆新的相機租賃請求已提交：\n\n"
                    f"相機名稱: {camera.name}\n"
                    f"租賃者: {rental.user_name}\n"
                    f"電子郵件: {rental.email}\n" # 包含使用者 Email
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
                user_subject = f"您的相機租賃請求已收到 - {camera.name}"
                user_message = (
                    f"親愛的 {rental.user_name}：\n\n"
                    f"感謝您在相機租約中心提交的租賃請求！\n\n"
                    f"您的訂單詳情如下：\n"
                    f"相機名稱: {camera.name}\n"
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
                user_recipient_list = [rental.email] # 發送到使用者提供的 Email

                try:
                    # 發送給管理員
                    send_mail(admin_subject, admin_message, admin_from_email, admin_recipient_list, fail_silently=False)
                    print(f"成功發送租賃通知 Email 給管理員 ({settings.ADMIN_EMAIL})")

                    # 發送給使用者
                    send_mail(user_subject, user_message, user_from_email, user_recipient_list, fail_silently=False)
                    print(f"成功發送租賃確認 Email 給使用者 ({rental.email})")

                except Exception as e:
                    print(f"發送 Email 失敗：{e}")
                    # 在生產環境中，這裡可以記錄錯誤或發送錯誤通知給開發者

                return redirect('my_rentals') # 租賃成功後導向我的租賃頁面
        else:
            # 如果表單驗證失敗，重新渲染詳情頁面並顯示錯誤
            return render(request, 'rental_app/camera_detail.html', {'camera': camera, 'form': form})
    return redirect('camera_detail', pk=pk) # 非 POST 請求導回詳情頁

def my_rentals(request):
    """
    顯示用戶（此處為模擬用戶）的所有租賃訂單。
    """
    # 由於沒有實際用戶認證，這裡只顯示所有訂單作為示範
    # 實際應用中會根據 request.user 過濾
    rentals = Rental.objects.all()
    return render(request, 'rental_app/my_rentals.html', {'rentals': rentals})

def about_us(request):
    """
    顯示關於我們頁面。
    """
    return render(request, 'rental_app/about_us.html')
