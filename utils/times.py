from django.utils import timezone
from dateutil.relativedelta import relativedelta  # 需要安装python-dateutil包


def default_start_date():
    return timezone.now().date()


def default_end_date():
    return timezone.now().date() + relativedelta(years=1)


time_format = '%Y-%m-%dT%H:%M:%SZ'
