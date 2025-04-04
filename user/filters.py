import django_filters
from .models import Jobseeker
class JobseekerFilter(django_filters.FilterSet):
    id = django_filters.CharFilter(field_name="id", lookup_expr="icontains")
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    experience = django_filters.CharFilter(field_name="experience", lookup_expr="icontains")
    skills = django_filters.CharFilter(field_name="skills", lookup_expr="icontains")
    location = django_filters.CharFilter(field_name="location", lookup_expr="icontains")

    class Meta:
        model = Jobseeker
        fields = ['id', 'name', 'experience', 'skills', 'location']

