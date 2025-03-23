#url mappings for user api
from django.urls import path
from . import views

urlpatterns = [
    path('create-user/', views.CreateUserView.as_view(), name='create-user'),
    path('token-user/', views.CreateTokenView.as_view(), name='token-user'),
    path('me-user/', views.ManageUserView.as_view(), name='me-user'),
    path('profile-user/', views.UpdateUserProfileView.as_view(), name='profile-user')
]