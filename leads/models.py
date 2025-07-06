from django.db import models
from multiselectfield import MultiSelectField # 多選第三方套件
from django.conf import settings # 帶入user

# 潛在客戶區塊
class PotentialCustomer(models.Model):
	# 下拉選單建立
	# 會跨表單的我用Class,其他的就簡單做tuple list了
	class CurrencyChoices(models.TextChoices):
		NTD = 'NTD','新台幣'
		USD = 'USD','美金'
		EUR = 'EUR','歐元'
		JPY = 'JPY','日幣'
	class CountryChoices(models.TextChoices):
		USA = 'USA','美國'
		TAIWAN = 'TAIWAN','台灣'
		JAPAN = 'JAPAN','日本'
		DENMARK = 'DENMARK','丹麥'
		GERMANY = 'GERMANY','德國'
		SWEDEN = 'SWEDEN','瑞典'
		CANADA = 'CANADA','加拿大'
		SWITZERLAND = 'SWITZERLAND','瑞士'
		ITALY = 'ITALY','義大利'
		FRANCE = 'FRANCE','法國'
	STATUS_CHOICES = [
		('uncontacted','未聯絡'),
		('contacted','開發中'),
		('deal','已成交'),
		('refused','拒絕往來')
	]
	RANK_CHOICES = [
		('A','A'),
		('B','B'),
		('C','C')
	]
	COMPANY_TYPE_CHOICES = [
		('resale','貿易轉售'),
		('die_maker','模具設計/製造'),
		('stamping','金屬沖壓'),
		('injection','塑膠射出'),
		('misc','其他')
	]
	INDUSTRY_CHOICES = [
		('aerospace','航太'),
		('automotive','汽車模具'),
		('electronic','電子'),
		('semi-conductor','半導體'),
		('medical','醫療'),
		('automation','自動化'),
		('architectural','建築'),
		('food','食品'),
		('others','其他')
	]
	SOURCE_CHOICES = [
		('website','博威官網'),
		('event','展覽開發'),
		('search','搜尋引擎'),
		('introduced','客戶轉介')
	]
	potential_customer_id = models.AutoField(primary_key=True,verbose_name="潛在客戶編號")
	company_name = models.CharField(max_length=100,blank=False,verbose_name='公司名稱')
	country = models.CharField(max_length=30,choices=CountryChoices.choices, blank=False,verbose_name='國家')
	address = models.CharField(max_length=200,blank=True,verbose_name='公司地址')
	phone = models.CharField(max_length=20,blank=True,verbose_name='連絡電話')
	email = models.EmailField(blank=True,verbose_name='電子郵件')
	website = models.URLField(blank=True,verbose_name='公司網址')
	currency = models.CharField(max_length=5,choices=CurrencyChoices.choices, blank=False,verbose_name='交易幣別')
	status = models.CharField(max_length=50,choices=STATUS_CHOICES,blank=False,default='uncontacted',verbose_name='狀態')
	company_type = models.CharField(max_length=30,choices=COMPANY_TYPE_CHOICES, blank=False,verbose_name='公司類型')
	industries = MultiSelectField(choices=INDUSTRY_CHOICES, max_length=100, blank=True,verbose_name='產業別')
	required_products = models.CharField(max_length=200,blank=True,verbose_name='需求品項')
	rank = models.CharField(max_length=5,choices=RANK_CHOICES, blank=True, verbose_name='客戶評級')
	source = models.CharField(max_length=30,choices=SOURCE_CHOICES,blank=True, verbose_name='客戶來源')
	sales_incharge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,verbose_name='業務人員')
	is_visitable = models.BooleanField(default=False, verbose_name="安排可拜訪")
	created_at = models.DateTimeField(auto_now_add=True,verbose_name='建立日期')
	updated_at = models.DateTimeField(auto_now=True,verbose_name='最後更新')
	notes = models.TextField(blank=True,verbose_name='備註')
	is_pinned = models.BooleanField(default=False, verbose_name='重點關注')

	# 這個方法會返回一個包含所選產業"標籤"的乾淨列表。
	@property
	def get_industries_labels(self):
		if not self.industries:
			return []
		choices_dict = dict(self.INDUSTRY_CHOICES)
		# 取得儲存的 choices，例如 [('automotive', '汽車產業'), ...]
		# self.industries 會返回一個 key 的列表，例如 ['automotive', 'aerospace']
		# 用來從 choices_dict 中查找對應的標籤
		selected_labels = [choices_dict.get(key) for key in self.industries]
		return selected_labels

	def __str__(self):
		return self.company_name

# 聯絡人區塊
class Contacts(models.Model):
	potential_customer = models.ForeignKey(PotentialCustomer, on_delete=models.CASCADE, null=True, verbose_name='關聯客戶',related_name='contacts')
	name = models.CharField(max_length=100,blank=True,verbose_name='聯絡人')
	position = models.CharField(max_length=100,blank=True,verbose_name='職稱')
	phone = models.CharField(max_length=20,blank=True,verbose_name='電話')
	email = models.EmailField(blank=True,verbose_name='電子郵件')
	notes = models.TextField(blank=True,verbose_name='備註')
	def __str__(self):
		return f'{self.name}({self.potential_customer.company_name})'

# 聯絡紀錄區塊
class ContactLogs(models.Model):
	potential_customer = models.ForeignKey(PotentialCustomer, on_delete=models.CASCADE, null=True, verbose_name='關聯客戶',related_name='logs')
	contact = models.ForeignKey(Contacts, on_delete=models.SET_NULL, null=True, verbose_name='聯絡人')
	topic = models.CharField(max_length=30,blank=False,verbose_name='主旨')
	content = models.TextField(blank=True,verbose_name='聯絡內容')
	created_at = models.DateTimeField(auto_now_add=True,verbose_name='聯絡日期')
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='業務人員')
	def __str__(self):
		return f'{self.potential_customer.company_name}-{self.topic}'