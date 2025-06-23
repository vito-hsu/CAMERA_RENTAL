# rental_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # 將根路徑指向 homepage 視圖 (首頁)
    path('', views.homepage, name='homepage'), 
    
    # 新增一個 URL 模式，用於顯示所有商品 (使用 item_list 視圖，但不傳遞 category)
    path('items/', views.item_list, name='all_items_list'), # <-- 新增這行，名稱為 'all_items_list'

    # 各類別商品列表頁面 (繼續使用 item_list 視圖，傳遞 category)
    path('cameras/', views.item_list, {'category': 'camera'}, name='camera_list'),
    path('lenses/', views.item_list, {'category': 'lens'}, name='lens_list'),
    path('others/', views.item_list, {'category': 'other'}, name='other_list'),

    # 商品詳情頁面 (通用)
    path('items/<int:pk>/', views.item_detail, name='item_detail'),
    # 商品租賃處理 (通用)
    path('items/<int:pk>/rent/', views.rent_item, name='rent_item'),

    # 我的租賃 (所有租賃訂單)
    path('my-rentals/', views.my_rentals, name='my_rentals'),
    # 關於我們
    path('about-us/', views.about_us, name='about_us'),
    # 聯繫我們
    path('contact/', views.contact_us_view, name='contact_us'),

    # 商品關鍵字搜尋頁面
    path('search/', views.product_search_view, name='product_search'),

    # 新增租賃規章
    path('rental-terms/', views.rental_terms, name='rental_terms'),
]