import django_filters
from .models import Jobseeker, Company
class JobseekerFilter(django_filters.FilterSet):
    id = django_filters.CharFilter(field_name="id", lookup_expr="icontains")
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    # experience = django_filters.CharFilter(field_name="experience", lookup_expr="icontains")
    skills = django_filters.CharFilter(field_name="skills", lookup_expr="icontains")
    location = django_filters.BaseInFilter(field_name="location", lookup_expr="in")
    specialization = django_filters.CharFilter(field_name="specialization", lookup_expr="icontains")
    seniority = django_filters.BaseInFilter(field_name="seniority", lookup_expr="in")
    track = django_filters.NumberFilter(field_name='track__id')
    branch = django_filters.NumberFilter(field_name='branch__id')
    track_name = django_filters.BaseInFilter(field_name='track__name', lookup_expr='in')
    branch_name = django_filters.BaseInFilter(field_name='branch__name', lookup_expr='in')
    iti_grad_year = django_filters.BaseInFilter(field_name="iti_grad_year", lookup_expr="in")


    class Meta:
        model = Jobseeker
        fields = ['id', 'name', 'seniority', 'skills', 'specialization', 'track', 'branch', 'track_name', 'branch_name']

class CompanyFilter(django_filters.FilterSet):
    id = django_filters.CharFilter(field_name="id", lookup_expr="icontains")
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    email = django_filters.CharFilter(field_name="email", lookup_expr="icontains")

    class Meta:
        model = Company
        fields = ['id', 'name', 'email']
