# 這個context_processorts是用來讀取Django內建的log訊息
from django.contrib.admin.models import LogEntry

def activity_log_processor(request):
    # 預設不回傳任何 log
    logs = []

    # 使用需登入
    if request.user.is_authenticated:
        # 取得最新的 15 筆操作紀錄
        # select_related 用於優化查詢，一次性取得關聯的 User 和 ContentType 資料，避免 N+1 查詢
        logs = LogEntry.objects.select_related('user', 'content_type').all()[:15]

    # 回傳一個字典，key 會成為模板中的變數名稱
    return {'recent_activity_logs': logs}