# chess_backend/urls.py

from django.contrib import admin
from django.urls import path, include
from accounts.views import RegisterView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),  # ✅ Make sure this is here

    
    # # Auth routes
    # path('api/auth/register/', RegisterView.as_view(), name='register'),
    # path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # # Optional: protected test
    # path('api/auth/protected/', include('accounts.urls')),  # only if you already have a protected endpoint
]
