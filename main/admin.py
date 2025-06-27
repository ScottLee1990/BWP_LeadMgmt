# main/admin.py

from django.contrib import admin
from .models import DashboardGoal # 導入我們的新模型

@admin.register(DashboardGoal)
class DashboardGoalAdmin(admin.ModelAdmin):
    list_display = ('get_period_display', 'new_customer_target', 'new_enquiry_target', 'enquiry_amount_target', 'success_amount_target')
    # 讓欄位可以直接在列表頁編輯
    list_editable = ('new_customer_target', 'new_enquiry_target', 'enquiry_amount_target', 'success_amount_target')