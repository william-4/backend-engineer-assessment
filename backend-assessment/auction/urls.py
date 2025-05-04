from django.urls import path
from .views import SignUpView, LoginView, LogoutView, NewAuctionView, EnterBidView, AdminAuctionView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Login
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh token
    path('api/signup/', SignUpView.as_view(), name='signup'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/auction/', NewAuctionView.as_view(), name='new_auction'),
    path('api/bid/', EnterBidView.as_view(), name='enter_bid'),
    path('api/admin/auction/', AdminAuctionView.as_view(), name='admin_auction'),
]
