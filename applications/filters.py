import django_filters
from .models import Application

class ApplicationFilter(django_filters.FilterSet):
    user = django_filters.BaseInFilter(field_name="user", lookup_expr="in")
    job = django_filters.BaseInFilter(field_name="job", lookup_expr="in")
    status = django_filters.CharFilter(field_name="status", lookup_expr="in")

    class Meta:
        model = Application
        fields = ['user', 'job', 'status']
