import django_filters
from .models import Job
 
class JobFilter(django_filters.FilterSet):
    # specialization = django_filters.CharFilter(method='custom_filter')
    attend = django_filters.CharFilter(method='custom_filter')
    type_of_job = django_filters.CharFilter(method='custom_filter')
    # experience = django_filters.CharFilter(method='custom_filter')

    def custom_filter(self, queryset, name, value):
        if value:
            values = [v.strip() for v in value.split(',')]
            if name == 'type_of_job':
                queryset = queryset.filter(type_of_job__in=values)
            elif name == 'attend':
                queryset = queryset.filter(attend__in=values)
            elif name == 'specialization':
                queryset = queryset.filter(specialization__in=values)
            # elif name == 'experience':
            #     queryset = queryset.filter(experience__in=values)
            return queryset
        return queryset
    id=django_filters.CharFilter(field_name="id", lookup_expr="icontains")
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    location = django_filters.CharFilter(field_name="location", lookup_expr="icontains")
    experince = django_filters.BaseInFilter(field_name="experince", lookup_expr="in")
    # type_of_job = django_filters.CharFilter(field_name="type_of_job", lookup_expr="in")
    company = django_filters.CharFilter(field_name="company")
    status = django_filters.CharFilter(field_name="status", lookup_expr="icontains")
    # attend =django_filters.CharFilter(field_name="attend", lookup_expr="in")
    company_name = django_filters.CharFilter(field_name="company__name", lookup_expr="icontains")
    specialization = django_filters.BaseInFilter(field_name="specialization", lookup_expr="in")

    class Meta:
        model = Job
        fields = ['id', 'title', 'location', 'experince', 'type_of_job', 'company', 'status', 'attend', 'specialization', 'company_name']