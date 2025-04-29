import django_filters
from .models import Jobseeker, Company
class JobseekerFilter(django_filters.FilterSet):
    id = django_filters.CharFilter(field_name="id", lookup_expr="icontains")
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    # experience = django_filters.CharFilter(field_name="experience", lookup_expr="icontains")
    skills = django_filters.CharFilter(field_name="skills", lookup_expr="icontains")
    location = django_filters.CharFilter(field_name="location", lookup_expr="icontains")
    specialization = django_filters.CharFilter(field_name="specialization", lookup_expr="icontains")
    seniority = django_filters.BaseInFilter(field_name="seniority", lookup_expr="in")

    class Meta:
        model = Jobseeker
        fields = ['id', 'name', 'seniority', 'skills', 'specialization']

class CompanyFilter(django_filters.FilterSet):
    id = django_filters.CharFilter(field_name="id", lookup_expr="icontains")
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    email = django_filters.CharFilter(field_name="email", lookup_expr="icontains")

    class Meta:
        model = Company
        fields = ['id', 'name', 'email']
