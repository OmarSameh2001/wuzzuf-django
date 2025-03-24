#url mappings for user api
from django.urls import path
from . import views
# from .views import ProcessCVATSView
urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.CreateTokenView.as_view(), name='token'),
    path('me/', views.ManageUserView.as_view(), name='me'),
    path('profile/', views.UpdateUserProfileView.as_view(), name='profile'),
    # path("process-cv/", ProcessCVATSView.as_view(), name="process_cv"),
]
