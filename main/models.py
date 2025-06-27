# main/models.py

from django.db import models

class DashboardGoal(models.Model):
    PERIOD_CHOICES = [
        ('monthly', '本月目標'),
        ('quarterly', '本季目標'),
        ('yearly', '年度目標'),
    ]

    period = models.CharField(
        max_length=10,
        choices=PERIOD_CHOICES,
        unique=True, # 確保每個週期只有一筆目標
        primary_key=True, # 直接用週期作為主鍵，更簡潔
        verbose_name='統計週期'
    )
    # 客戶相關目標
    # 【修改】將 new_customer_target 的 verbose_name 改為「新成交客戶數目標」
    # 這樣在後台的顯示才會是正確的
    new_customer_target = models.PositiveIntegerField(default=10, verbose_name='新成交客戶數目標')

    # 報價相關目標
    new_enquiry_target = models.PositiveIntegerField(default=20, verbose_name='新增報價數目標')
    enquiry_amount_target = models.DecimalField(max_digits=12, decimal_places=2, default=500000.00, verbose_name='新增報價總金額目標')
    success_amount_target = models.DecimalField(max_digits=12, decimal_places=2, default=100000.00, verbose_name='成交總金額目標')

    def __str__(self):
        return self.get_period_display()

    class Meta:
        verbose_name = '儀表板目標設定'
        verbose_name_plural = '儀表板目標設定'