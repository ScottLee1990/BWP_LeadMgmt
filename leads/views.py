#  views.py
'''
處理與PotentialCustomer、Contacts、ContactLogs這三個Model相關request
包含完整的CRUD，並加入了使用者身份驗證、排序、篩選、分頁、操作紀錄和資料匯出等附加功能。
'''

import csv

from django.contrib.auth.decorators import login_required
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q, Max
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import escape_uri_path

from .forms import ContactsForm, PotentialCustomerForm, ContactLogsForm
from .models import PotentialCustomer, Contacts, ContactLogs

# 所有使用的套件於上方匯入

# -----輔助函式---------------------------------------------------------------------------

# 後續list和輸出的部分都會套運查詢、篩選邏輯，在這個輔助函式管理
# 根據前端回傳的filter做QuerySet的篩選和排序
def _get_filtered_customers_queryset(request):
    query = request.GET.get('q', '') # 公司名、產業...等等
    rank_filter = request.GET.get('rank', '') # 評級
    status_filter = request.GET.get('status', '') # 狀態
    owner_filter = request.GET.get('owner', '') # 負責人
    sort_field = request.GET.get('sort', 'last_contacted_at') # 預設排序為最後聯絡時間
    sort_order = request.GET.get('order', 'desc')

    # 用annotate和Max動態計算每個客戶的最後聯絡時間, annotate超好用
    # 在potential_customer新增一個'last_contacted_at'的臨時屬性
    # 處理QuerySet時，實際上還沒有內容存在，用__讓SQL理解跨模型連結
    potential_customers = PotentialCustomer.objects.annotate(
        last_contacted_at=Max('logs__created_at') # logs是ContactLogs的related_name,用Max找出最大值也就是最後聯絡時間
    )
    # 用上面get取得的值，對QuerySet增加過濾條件
    # Q是用來判斷多重條件
    if query:
        potential_customers = potential_customers.filter(
            Q(company_name__icontains=query) |
            Q(industries__icontains=query) |
            Q(required_products__icontains=query)
        )
    if rank_filter:
        potential_customers = potential_customers.filter(rank=rank_filter)
    if status_filter:
        potential_customers = potential_customers.filter(status=status_filter)
    if owner_filter:
        potential_customers = potential_customers.filter(sales_incharge__username=owner_filter)

    # 可排序的欄位列表,防止使用者找出隱藏資訊做排序
    valid_sort_fields = {'company_name', 'country', 'rank', 'status', 'created_at', 'last_contacted_at'}
    sort_by = sort_field if sort_field in valid_sort_fields else 'last_contacted_at'
    # order_by根據有無'-'來判斷做decs或asc
    if sort_order == 'desc':
        sort_by = '-' + sort_by

    return potential_customers.order_by(sort_by)

# -----PotentialCustomer的CRUD---------------------------------------------------------------------------

# 潛在客戶總表,讀取過濾後的QuerySet並用Paginator包裝後回傳
@login_required
def potential_customer_list(request):
    # 取得套用查詢過濾器的QuerySet
    potential_customers_qs = _get_filtered_customers_queryset(request)
    # 將QuerySet用Paginator做分頁包裝
    paginator = Paginator(potential_customers_qs, 20)
    page = request.GET.get('page')

    # 這邊是確保page是有效的,若非數字就跳到第1頁，若超過最大頁數則顯示最後一頁
    try:
        potential_customers = paginator.page(page)
    except PageNotAnInteger:
        potential_customers = paginator.page(1)
    except EmptyPage:
        potential_customers = paginator.page(paginator.num_pages)

    # 設定篩選器的選項
    # 從PotentialCustomer中取得所有的sales_incharge__username做為篩選器的選項,用.distinct確保不重複
    owners = PotentialCustomer.objects.values_list('sales_incharge__username', flat=True).distinct()
    rank_choices = PotentialCustomer.RANK_CHOICES
    status_choices = PotentialCustomer.STATUS_CHOICES

    return render(request, 'leads/potential_customer_list.html', {
        'potential_customers': potential_customers,
        'owners': owners,
        'rank_choices': rank_choices,
        'status_choices': status_choices,
        # 下面這些篩選器會隨著GET和前端作互動
        'query': request.GET.get('q', ''),
        'rank_filter': request.GET.get('rank', ''),
        'status_filter': request.GET.get('status', ''),
        'owner_filter': request.GET.get('owner', ''),
        'sort_field': request.GET.get('sort', 'created_at'),
        'sort_order': request.GET.get('order', 'desc'),
    })

# 客戶詳細頁面
# 用django內建的get_object_or_404簡單的用pk抓取對應的PotentialCustomer物件並回傳
# get_object_or_404本身已包含try...except邏輯,好用
@login_required
def potential_customer_detail(request, pk):
    potential_customer = get_object_or_404(PotentialCustomer, pk=pk)
    return render(request, 'leads/potential_customer_detail.html', context={'potential_customer': potential_customer})

# 建立新潛在客戶,user第一次連線時request是GET、回傳空白的form，而user點擊submit後會送出POST的request並儲存表單
@login_required
def potential_customer_create(request):
    # 前端submit表單
    if request.method == 'POST':
        form = PotentialCustomerForm(request.POST)
        # 檢查格式和必填
        # 暫存表單後由後端將操作者填到sales_incharge欄位才儲存
        if form.is_valid():
            potential_customer = form.save(commit=False)
            potential_customer.sales_incharge = request.user
            potential_customer.save()

            # 寫入操作紀錄
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(potential_customer).id,
                object_id=potential_customer.pk,
                object_repr=str(potential_customer),
                action_flag=ADDITION,
                change_message="新增潛在客戶"
            )

            return redirect('leads:potential_customer_list')
    # 第一次連線時
    else:
        form = PotentialCustomerForm()
    return render(request, 'leads/potential_customer_form.html', context={'form': form})

# 更新客戶資料
# 用get_object_or_404和pk抓取已存在的PotentialCustomer的物件
@login_required
def potential_customer_update(request, pk):
    potential_customer = get_object_or_404(PotentialCustomer, pk=pk)
    # 前端submit表單
    if request.method == 'POST':
        form = PotentialCustomerForm(request.POST, instance=potential_customer)
        if form.is_valid():
            updated_customer = form.save()

            # 寫入操作紀錄
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(updated_customer).id,
                object_id=updated_customer.pk,
                object_repr=str(updated_customer),
                action_flag=CHANGE,
                change_message="編輯潛在客戶資料"
            )

            return redirect('leads:potential_customer_detail', pk=potential_customer.pk)
    # 第一次GET,先提供目前物件的資訊
    else:
        form = PotentialCustomerForm(instance=potential_customer)
    return render(request, 'leads/potential_customer_form.html', context={'form': form})

# 刪除客戶資料,結合前端modal
@login_required
def potential_customer_delete(request, pk):
    potential_customer = get_object_or_404(PotentialCustomer, pk=pk)
    # 前端點擊確認
    if request.method == 'POST':
        customer_repr = str(potential_customer)  # 在刪除前先取得物件的文字表示
        # django的內建刪除語法
        potential_customer.delete()

        # 寫入操作紀錄
        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=ContentType.objects.get_for_model(PotentialCustomer).id,  # 物件已刪，需直接用模型
            object_id=pk,
            object_repr=customer_repr,
            action_flag=DELETION,
            change_message="刪除潛在客戶"
        )
        # 前端收到下面的json表示操作順利完成
        return JsonResponse({'success': True})
    # 第一次request,將物件資料用json提供給前端modal做渲染
    else:
        html_form = render_to_string('leads/potential_customer_delete_modal.html', {
            'potential_customer': potential_customer
        }, request=request)
        return JsonResponse({'html_form': html_form})

# 設定關注客戶
# 簡單的用pk取得並調整物件屬性後用save()儲存修改
@login_required
def toggle_pin(request, pk):
    potential_customer = get_object_or_404(PotentialCustomer, pk=pk)
    potential_customer.is_pinned = not potential_customer.is_pinned
    potential_customer.save()

    # 寫入操作紀錄
    change_message = "置頂客戶" if potential_customer.is_pinned else "取消置頂客戶"
    LogEntry.objects.log_action(
        user_id=request.user.id,
        content_type_id=ContentType.objects.get_for_model(potential_customer).id,
        object_id=potential_customer.pk,
        object_repr=str(potential_customer),
        action_flag=CHANGE,
        change_message=change_message
    )
    return redirect('leads:potential_customer_detail', pk=pk)


# -----Contacts的CRUD---------------------------------------------------------------------------

# 大致上和PotentialCustomer的CRUD邏輯相同,唯獨包含create和update也都使用回傳Json給前端Modal的方式
# 需有PotentialCustomer才能建立Contact
@login_required
def contact_create(request, pk):
    potential_customer = get_object_or_404(PotentialCustomer, pk=pk)
    if request.method == 'POST':
        form = ContactsForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.potential_customer = potential_customer
            contact.save()

            # 寫入操作紀錄
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(contact).id,
                object_id=contact.pk,
                object_repr=f"{str(contact)} (屬於 {str(potential_customer)})",
                action_flag=ADDITION,
                change_message="新增聯絡人"
            )
            return JsonResponse({'success': True})
    else:
        form = ContactsForm()
    # 這邊是把template,form,potential_customer和form_action打包成html字串,再回傳JS可讀的Json
    html_form = render_to_string('leads/contact_form_modal.html', {
        'form': form,
        'potential_customer': potential_customer,
        'form_action': reverse('leads:contact_create', args=[potential_customer.pk]),
    }, request=request)
    return JsonResponse({'html_form': html_form})


@login_required
def contact_update(request, pk):
    contact = get_object_or_404(Contacts, pk=pk)
    if request.method == 'POST':
        form = ContactsForm(request.POST, instance=contact)
        if form.is_valid():
            updated_contact = form.save()

            # 寫入操作紀錄
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(updated_contact).id,
                object_id=updated_contact.pk,
                object_repr=f"{str(updated_contact)} (屬於 {str(contact.potential_customer)})",
                action_flag=CHANGE,
                change_message="編輯聯絡人"
            )
            return JsonResponse({'success': True})
    else:
        form = ContactsForm(instance=contact)

    html_form = render_to_string('leads/contact_form_modal.html', {
        'form': form,
        'potential_customer': contact.potential_customer,
        'form_action': reverse('leads:contact_update', args=[contact.id])
    }, request=request)
    return JsonResponse({'html_form': html_form})


@login_required
def contact_delete(request, pk):
    contact = get_object_or_404(Contacts, pk=pk)
    if request.method == 'POST':
        contact_repr = f"{str(contact)} (屬於 {str(contact.potential_customer)})"  # 在刪除前先取得物件的文字表示
        contact.delete()

        # 寫入操作紀錄
        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=ContentType.objects.get_for_model(Contacts).id,  # 物件已刪，需直接用模型
            object_id=pk,
            object_repr=contact_repr,
            action_flag=DELETION,
            change_message="刪除聯絡人"
        )
        return JsonResponse({'success': True})
    else:
        html_form = render_to_string('leads/contact_delete_modal.html', {'contact': contact}, request=request)
        return JsonResponse({'html_form': html_form})


# -----ContactLogs的CRUD---------------------------------------------------------------------------

# 和Contacts的CRUD邏輯幾乎相同
# 需有PotentialCustomer才能建立ContactLog
@login_required
def contact_log_create(request, pk):
    potential_customer = get_object_or_404(PotentialCustomer, pk=pk)
    if request.method == 'POST':
        form = ContactLogsForm(request.POST, potential_customer=potential_customer)
        if form.is_valid():
            log = form.save(commit=False)
            log.potential_customer = potential_customer
            log.created_by = request.user
            log.save()
            # 改用annotate提供last_contacted_at了，註解掉這個
            # potential_customer.last_contacted_at = log.created_at
            # potential_customer.save()
            return JsonResponse({'success': True})
    else:
        form = ContactLogsForm(potential_customer=potential_customer)
    html_form = render_to_string('leads/contactlog_form_modal.html', {
        'form': form, 'potential_customer': potential_customer,
        'form_action': reverse('leads:contact_log_create', args=[potential_customer.pk]),
        'title': '新增開發紀錄'
    }, request=request)
    return JsonResponse({'html_form': html_form})


@login_required
def contact_log_update(request, pk):
    log = get_object_or_404(ContactLogs, pk=pk)
    potential_customer = log.potential_customer
    if request.method == 'POST':
        form = ContactLogsForm(request.POST, instance=log, potential_customer=potential_customer)
        if form.is_valid():
            form.save()
            # 改用annotate提供last_contacted_at了，註解掉這個
            # potential_customer.last_contacted_at = log.created_at
            # potential_customer.save()
            return JsonResponse({'success': True})
    else:
        form = ContactLogsForm(instance=log, potential_customer=potential_customer)
    html_form = render_to_string('leads/contactlog_form_modal.html', {
        'form': form, 'potential_customer': potential_customer,
        'form_action': reverse('leads:contact_log_update', args=[pk]), 'title': '編輯開發紀錄'
    }, request=request)
    return JsonResponse({'html_form': html_form})


@login_required
def contact_log_delete(request, pk):
    log = get_object_or_404(ContactLogs, pk=pk)
    # 多一個操作者的驗證機制
    if log.created_by != request.user:
        return HttpResponseForbidden("你不是這筆開發紀錄的建立者")
    if request.method == 'POST':
        log.delete()
        return JsonResponse({'success': True})
    html_form = render_to_string('leads/contactlog_delete_modal.html', {'log': log}, request=request)
    return JsonResponse({'html_form': html_form})


# -----匯出csv---------------------------------------------------------------------------

@login_required
def export_customers_csv(request):
    potential_customers = _get_filtered_customers_queryset(request)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response.write('\ufeff')  # 加入 BOM，讓 Excel 正確辨識 UTF-8
    filename = escape_uri_path(f"潛在客戶清單_{timezone.now().date()}.csv")
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['公司名稱', '國家', '評級', '狀態', '業務負責', '最後聯絡', '建立時間'])

    for c in potential_customers:
        writer.writerow([
            c.company_name,
            c.get_country_display(),
            c.get_rank_display(),  # 使用 get_FOO_display 獲取 choice 的可讀名稱
            c.get_status_display(),
            c.sales_incharge.username if c.sales_incharge else '',
            c.last_contacted_at.strftime('%Y-%m-%d') if c.last_contacted_at else '',
            c.created_at.strftime('%Y-%m-%d %H:%M'),
        ])

    return response