from django.urls import path
from accounts.views import (
    RegisterUserView, LoginView, LogoutView, ForgotPasswordView, VerifyOtpView, ResetPasswordView, UserListView, ProfileViewUpdate
)

urlpatterns = [
    path('auth/register/', RegisterUserView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/forgot_password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('auth/verify_otp/', VerifyOtpView.as_view(), name='verify_otp'),
    path('auth/reset_password/', ResetPasswordView.as_view(), name='reset_password'),

    path('users/', UserListView.as_view(), name='users_list'),
    path('profile/', ProfileViewUpdate.as_view(), name='users-detail'),
    path('profile/update/<int:id>/', ProfileViewUpdate.as_view(), name='users-update'),
]
