# lead_enquiries/urls.py

from . import views
from django.urls import path

app_name = 'lead_enquiries'

urlpatterns = [
    # ==================================
    # 報價單 (Enquiry) 的主要頁面 URL
    # ==================================
    # 列表頁 (e.g., /enquiries/)
    path('', views.enquiry_list, name='enquiry_list'),

    # 新增頁 (e.g., /enquiries/create/)
    path('create/', views.enquiry_create, name='enquiry_create'),

    # 詳情頁 (e.g., /enquiries/detail/1/)
    path('detail/<int:pk>/', views.enquiry_detail, name='enquiry_detail'),

    # 修改頁 (e.g., /enquiries/detail/1/update/)
    path('detail/<int:pk>/update/', views.enquiry_update, name='enquiry_update'),

    # 刪除功能 (AJAX) (e.g., /enquiries/delete/1/)
    path('delete/<int:pk>/', views.enquiry_delete, name='enquiry_delete'),

    # ==================================
    # 報價單品項 (EnquiryItem) 的 AJAX URL
    # ==================================
    # 在詳情頁新增品項 (需要報價單的 pk)
    path('detail/<int:enquiry_pk>/items/add/', views.enquiry_item_create, name='enquiry_item_create'),

    # 修改特定品項 (需要品項本身的 pk)
    path('items/update/<int:pk>/', views.enquiry_item_update, name='enquiry_item_update'),

    # 刪除特定品項 (需要品項本身的 pk)
    path('items/delete/<int:pk>/', views.enquiry_item_delete, name='enquiry_item_delete'),

    # ==================================
    # 報價單追蹤 (EnquiryTrack) 的 AJAX URL
    # ==================================
    # 在詳情頁新增追蹤紀錄 (需要報價單的 pk)
    path('detail/<int:enquiry_pk>/tracks/add/', views.enquiry_track_create, name='enquiry_track_create'),

    # 修改特定追蹤紀錄 (需要紀錄本身的 pk)
    path('tracks/update/<int:pk>/', views.enquiry_track_update, name='enquiry_track_update'),

    # 刪除特定追蹤紀錄 (需要紀錄本身的 pk)
    path('tracks/delete/<int:pk>/', views.enquiry_track_delete, name='enquiry_track_delete'),

    # ==================================
    # 其他功能 URL
    # ==================================
    # 重點追蹤功能
    path('detail/<int:pk>/toggle_pin/', views.toggle_enquiry_pin, name='toggle_enquiry_pin'),

    # 匯出 CSV
    path('export_csv/', views.export_enquiries_csv, name='export_enquiries_csv'),
    path('detail/<int:enquiry_pk>/attachments/upload/', views.enquiry_attachment_upload,
         name='enquiry_attachment_upload'),
    path('attachments/delete/<int:pk>/', views.enquiry_attachment_delete, name='enquiry_attachment_delete'),
]