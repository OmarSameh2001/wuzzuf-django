import django_filters
from .models import Job
 
class JobFilter(django_filters.FilterSet):
    id=django_filters.CharFilter(field_name="id", lookup_expr="icontains")
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    location = django_filters.CharFilter(field_name="location", lookup_expr="icontains")
    experience = django_filters.CharFilter(field_name="experience", lookup_expr="icontains")
    type_of_job = django_filters.CharFilter(field_name="type_of_job", lookup_expr="icontains")

    class Meta:
        model = Job
        fields = ['id', 'title', 'location', 'experience', 'type_of_job']