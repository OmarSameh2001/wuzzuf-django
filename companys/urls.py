#url mappings for company api
from django.urls import path
from . import views

urlpatterns = [
    path('create-company/', views.CreateCompanyView.as_view(), name='create-company'),
    path('token-company/', views.CreateTokenView.as_view(), name='token-company'),
    path('me-company/', views.ManageCompanyView.as_view(), name='me-company'),
    path('profile-company/', views.UpdateCompanyProfileView.as_view(), name='profile-company')
]