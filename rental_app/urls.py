# rental_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.camera_list, name='camera_list'), # 相機列表首頁
    path('cameras/<int:pk>/', views.camera_detail, name='camera_detail'), # 相機詳情頁
    path('cameras/<int:pk>/rent/', views.rent_camera, name='rent_camera'), # 租賃相機處理
    path('my-rentals/', views.my_rentals, name='my_rentals'), # 我的租賃頁面
    path('about-us/', views.about_us, name='about_us'), # 新增關於我們頁面
]
