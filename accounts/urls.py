from django.urls import path
from .views import RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import ProtectedView
from .views import RegisterView, ProtectedView, UserProfileView
from .views import LogoutView
from django.urls import include



urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('protected/', ProtectedView.as_view(), name='protected'),
    path('profile/', UserProfileView.as_view(), name='profile'),  
    path('logout/', LogoutView.as_view(), name='logout'),



]
