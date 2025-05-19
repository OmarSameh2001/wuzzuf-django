import django_filters
from .models import Application

class ApplicationFilter(django_filters.FilterSet):
    user = django_filters.BaseInFilter(field_name="user", lookup_expr="in")
    job = django_filters.BaseInFilter(field_name="job", lookup_expr="in")
    status = django_filters.CharFilter(field_name="status", lookup_expr="in")
    company = django_filters.BaseInFilter(field_name="job__company", lookup_expr="in")
    company_name = django_filters.CharFilter(field_name="job__company__name", lookup_expr="icontains")
    job_title = django_filters.CharFilter(field_name="job__title", lookup_expr="icontains")
    fail = django_filters.BooleanFilter(field_name="fail")
    
    class Meta:
        model = Application
        fields = ['user', 'job', 'status', 'company', 'company_name', 'job_title', 'fail']
