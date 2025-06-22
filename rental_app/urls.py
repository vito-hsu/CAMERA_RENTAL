# rental_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # 網站首頁顯示所有商品
    path('', views.item_list, name='item_list'),

    # 各類別商品列表頁面
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

    # <--- 新增這一行：商品關鍵字搜尋頁面 --->
    path('search/', views.product_search_view, name='product_search'),
]