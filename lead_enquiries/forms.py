# lead_enquiries/forms.py
from django import forms
from .models import Enquiry, EnquiryItem, EnquiryTrack, EnquiryAttachment
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Fieldset


# ===================================================================
#  報價單主表單 (EnquiryForm)
#  使用 Crispy Forms 進行詳細佈局
# ===================================================================
class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        # 定義表單中需要顯示的欄位
        fields = [
            'bwp_no',
            'potential_customer',
            'enquiry_no',
            'status',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        # form_tag = False 讓我們可以在模板中自己控制 <form> 標籤和按鈕
        self.helper.form_tag = False

        # 參照您的 PotentialCustomerForm 風格來定義佈局
        self.helper.layout = Layout(
            Fieldset(
                '報價單主要資訊',
                Row(
                    Column('bwp_no', css_class='form-group col-md-6 mb-3'),
                    # potential_customer 欄位會自動渲染成一個下拉選單
                    Column('potential_customer', css_class='form-group col-md-6 mb-3'),
                ),
                Row(
                    Column('enquiry_no', css_class='form-group col-md-6 mb-3'),
                    Column('status', css_class='form-group col-md-6 mb-3'),
                )
            )
        )
        # 讓客戶下拉選單也套用 bootstrap 樣式
        self.fields['potential_customer'].widget.attrs.update({'class': 'form-select'})
        # 【新增】如果表單在初始化時有客戶資料，就把它設為唯讀
        if 'initial' in kwargs and 'potential_customer' in kwargs['initial']:
            self.fields['potential_customer'].disabled = True

# ===================================================================
#  報價單品項表單 (EnquiryItemForm)
#  用於 AJAX Modal 彈窗
# ===================================================================
class EnquiryItemForm(forms.ModelForm):
    class Meta:
        model = EnquiryItem
        # 排除在 view 中會自動設定的 enquiry 欄位
        exclude = ('enquiry',)
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 為所有欄位自動加上 bootstrap class，方便在 modal 中渲染
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


# ===================================================================
#  報價單追蹤紀錄表單 (EnquiryTrackForm)
#  用於 AJAX Modal 彈窗
# ===================================================================
class EnquiryTrackForm(forms.ModelForm):
    class Meta:
        model = EnquiryTrack
        # 排除在 view 中會自動設定的 enquiry 和 created_by 欄位
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5, 'placeholder': '請輸入追蹤內容...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget.attrs.update({'class': 'form-control'})

class EnquiryAttachmentForm(forms.ModelForm):
    class Meta:
        model = EnquiryAttachment
        fields = ['file', 'description']