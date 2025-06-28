#  views.py (Refactored and with Activity Log)

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

def _get_filtered_customers_queryset(request):
    #  處理查詢和排序邏輯
    query = request.GET.get('q', '')
    rank_filter = request.GET.get('rank', '')
    status_filter = request.GET.get('status', '')
    owner_filter = request.GET.get('owner', '')
    # 【修改】讓預設排序改為最後聯絡時間
    sort_field = request.GET.get('sort', 'last_contacted_at')
    sort_order = request.GET.get('order', 'desc')

    # 【核心修改】使用 annotate 和 Max 來動態計算每個客戶的最後聯絡時間
    # 這會為每一個 potential_customer 物件新增一個名為 'last_contacted_at' 的臨時屬性
    potential_customers = PotentialCustomer.objects.annotate(
        last_contacted_at=Max('logs__created_at') # 'logs' 是 ContactLogs 模型反向關聯的名稱
    )

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

    # 【修改】將我們 annotate 出來的 'last_contacted_at' 加入可排序的欄位列表
    valid_sort_fields = {'company_name', 'country', 'rank', 'status', 'created_at', 'last_contacted_at'}
    sort_by = sort_field if sort_field in valid_sort_fields else 'last_contacted_at'

    if sort_order == 'desc':
        sort_by = '-' + sort_by

    return potential_customers.order_by(sort_by)

@login_required
def potential_customer_list(request):
    # 查詢邏輯保持不變
    potential_customers_qs = _get_filtered_customers_queryset(request)

    owners = PotentialCustomer.objects.values_list('sales_incharge__username', flat=True).distinct()
    paginator = Paginator(potential_customers_qs, 20)
    page = request.GET.get('page')

    try:
        # 【最終修正】將分頁物件統一命名為 'potential_customers'
        potential_customers = paginator.page(page)
    except PageNotAnInteger:
        potential_customers = paginator.page(1)
    except EmptyPage:
        potential_customers = paginator.page(paginator.num_pages)

    rank_choices = PotentialCustomer.RANK_CHOICES
    status_choices = PotentialCustomer.STATUS_CHOICES

    return render(request, 'leads/potential_customer_list.html', {
        # 【最終修正】傳遞給模板的變數也統一為 'potential_customers'
        'potential_customers': potential_customers,
        'query': request.GET.get('q', ''),
        'rank_filter': request.GET.get('rank', ''),
        'status_filter': request.GET.get('status', ''),
        'owner_filter': request.GET.get('owner', ''),
        'owners': owners,
        'sort_field': request.GET.get('sort', 'created_at'),
        'sort_order': request.GET.get('order', 'desc'),
        'rank_choices': rank_choices,
        'status_choices': status_choices,
    })


@login_required
def potential_customer_detail(request, pk):
    potential_customer = get_object_or_404(PotentialCustomer, pk=pk)
    return render(request, 'leads/potential_customer_detail.html', context={'potential_customer': potential_customer})


@login_required
def potential_customer_create(request):
    if request.method == 'POST':
        form = PotentialCustomerForm(request.POST)
        if form.is_valid():
            potential_customer = form.save(commit=False)
            potential_customer.sales_incharge = request.user
            potential_customer.save()

            # --- 新增：寫入操作紀錄 ---
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(potential_customer).id,
                object_id=potential_customer.pk,
                object_repr=str(potential_customer),
                action_flag=ADDITION,
                change_message="新增潛在客戶"
            )

            return redirect('leads:potential_customer_list')
    else:
        form = PotentialCustomerForm()
    return render(request, 'leads/potential_customer_form.html', context={'form': form})


@login_required
def potential_customer_update(request, pk):
    potential_customer = get_object_or_404(PotentialCustomer, pk=pk)
    if request.method == 'POST':
        form = PotentialCustomerForm(request.POST, instance=potential_customer)
        if form.is_valid():
            updated_customer = form.save()

            # --- 修改：寫入操作紀錄 ---
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(updated_customer).id,
                object_id=updated_customer.pk,
                object_repr=str(updated_customer),
                action_flag=CHANGE,
                change_message="編輯潛在客戶資料"
            )

            return redirect('leads:potential_customer_detail', pk=potential_customer.pk)
    else:
        form = PotentialCustomerForm(instance=potential_customer)
    return render(request, 'leads/potential_customer_form.html', context={'form': form})


@login_required
def potential_customer_delete(request, pk):
    potential_customer = get_object_or_404(PotentialCustomer, pk=pk)
    if request.method == 'POST':
        customer_repr = str(potential_customer)  # 在刪除前先取得物件的文字表示

        potential_customer.delete()

        # --- 刪除：寫入操作紀錄 ---
        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=ContentType.objects.get_for_model(PotentialCustomer).id,  # 物件已刪，需直接用模型
            object_id=pk,
            object_repr=customer_repr,
            action_flag=DELETION,
            change_message="刪除潛在客戶"
        )
        return JsonResponse({'success': True})
    else:
        html_form = render_to_string('leads/potential_customer_delete_modal.html', {
            'potential_customer': potential_customer
        }, request=request)
        return JsonResponse({'html_form': html_form})


@login_required
def toggle_pin(request, pk):
    potential_customer = get_object_or_404(PotentialCustomer, pk=pk)
    potential_customer.is_pinned = not potential_customer.is_pinned
    potential_customer.save()

    # --- 修改：寫入操作紀錄 ---
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


# ===================================================================
#  聯絡人 (Contacts) 視圖
# ===================================================================

@login_required
def contact_create(request, pk):
    potential_customer = get_object_or_404(PotentialCustomer, pk=pk)
    if request.method == 'POST':
        form = ContactsForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.potential_customer = potential_customer
            contact.save()

            # --- 新增：寫入操作紀錄 ---
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

            # --- 修改：寫入操作紀錄 ---
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

        # --- 刪除：寫入操作紀錄 ---
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


# ===================================================================
#  開發紀錄 (ContactLogs) 視圖
#  註：此模型本身即為一種 "Log"，通常不需要再為其操作額外寫入 LogEntry，
#  避免紀錄中出現「新增了一筆新增紀錄」這樣的冗餘資訊。
#  因此，以下視圖保留原樣。
# ===================================================================

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
            potential_customer.last_contacted_at = log.created_at
            potential_customer.save()
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
            potential_customer.last_contacted_at = log.created_at
            potential_customer.save()
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
    if log.created_by != request.user:
        return HttpResponseForbidden("你不是這筆開發紀錄的建立者")
    if request.method == 'POST':
        log.delete()
        return JsonResponse({'success': True})
    html_form = render_to_string('leads/contactlog_delete_modal.html', {'log': log}, request=request)
    return JsonResponse({'html_form': html_form})


# ===================================================================
#  匯出功能 (Export)
# ===================================================================

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