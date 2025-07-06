from django.db import models
from django.contrib.auth.models import User
import os
from leads.models import PotentialCustomer

STATUS_CHOICES = [
    ('untracked', '未追蹤'),
    ('tracking', '追蹤中'),
    ('success', '已成交'),
    ('lost', '已失去')
    ]

# 報價單區塊
class Enquiry(models.Model):

    bwp_no = models.CharField(max_length=20, unique=True,verbose_name='博威報價單號',blank=False)
    potential_customer = models.ForeignKey(PotentialCustomer,blank=False,on_delete=models.CASCADE,verbose_name='客戶',related_name='enquiries')
    enquiry_no = models.CharField(max_length=20,blank=True,verbose_name='客戶報價單')
    status = models.CharField(choices=STATUS_CHOICES,default='untracked',max_length=20,verbose_name='追蹤狀態')
    is_pinned = models.BooleanField(default=False,verbose_name='重點追蹤')
    created_at = models.DateTimeField(auto_now_add=True,verbose_name='建立日期')
    updated_at = models.DateTimeField(auto_now=True,verbose_name='更新日期')
    created_by = models.ForeignKey(User,blank=False,on_delete=models.CASCADE,verbose_name='建立者')

    @property
    def currency(self): # 抓關聯客戶的幣別
        return self.potential_customer.currency

    @property
    def get_currency_display(self):
        return self.potential_customer.get_currency_display()

    # 計算原幣別總金額
    @property
    def total_amount(self):
        if not self.items.all():
            return 0
        return sum(item.subtotal for item in self.items.all() if item.subtotal is not None)

    # 計算台幣總金額
    @property
    def total_amount_ntd(self):
        if not self.items.all():
            return 0
        return sum(item.subtotal_ntd for item in self.items.all() if item.subtotal_ntd is not None)

    def __str__(self):
        return f'{self.bwp_no}'

# 報價品項
class EnquiryItem(models.Model):
    enquiry = models.ForeignKey(Enquiry,blank=False,on_delete=models.CASCADE,verbose_name='報價單',related_name='items')
    item_name = models.CharField(max_length=30,blank=True,verbose_name='產品名稱')
    item_spec = models.CharField(max_length=30,blank=True,verbose_name='產品規格')
    material = models.CharField(max_length=30,blank=True,verbose_name='材質')
    unit_price = models.FloatField(blank=True,verbose_name='單價')
    exchange_rate = models.FloatField(blank=True,verbose_name='匯率')
    quantity = models.IntegerField(blank=True,verbose_name='數量')
    cost = models.FloatField(blank=True,verbose_name='進價')
    cost_rate =models.FloatField(blank=True,verbose_name='進價匯率')
    supplier = models.CharField(max_length=30,blank=True,verbose_name='供應商')
    note = models.TextField(blank=True,verbose_name='備註')

    # 計算原幣別小計
    @property
    def subtotal(self):
        if self.quantity is not None and self.unit_price is not None:
            return self.quantity * self.unit_price
        return 0

    # 計算台幣小計
    @property
    def subtotal_ntd(self):
        rate = self.exchange_rate or 1.0
        return self.subtotal * rate

    def __str__(self):
        return f'{self.item_name}-{self.unit_price}-{self.quantity}'

# 報價追蹤區塊
class EnquiryTrack(models.Model):
    enquiry = models.ForeignKey(Enquiry,blank=False,on_delete=models.CASCADE,verbose_name='報價單',related_name='tracks')
    created_at = models.DateTimeField(auto_now_add=True,verbose_name='建立日期')
    content = models.TextField(blank=True,verbose_name='內容')
    created_by = models.ForeignKey(User,blank=False,on_delete=models.CASCADE,verbose_name='建立人')

    def __str__(self):
        return f'{self.enquiry.bwp_no}-{self.created_by.username}'

# 報價附件區塊
# 儲存路徑
def enquiry_attachment_path(instance, filename):
    return f'enquiries/{instance.enquiry.pk}/{filename}'

class EnquiryAttachment(models.Model):
    enquiry = models.ForeignKey(Enquiry, on_delete=models.CASCADE, verbose_name='報價單', related_name='attachments')
    file = models.FileField(upload_to=enquiry_attachment_path, verbose_name='檔案')
    description = models.CharField(max_length=255, blank=True, verbose_name='檔案描述')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='上傳時間')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='上傳者')

    class Meta:
        verbose_name = '報價單附件'
        verbose_name_plural = '報價單附件'

    def __str__(self):
        return os.path.basename(self.file.name)
