from .views import registerationview,UsernameValidationview,EmailValidationview, \
    RequestPasswordResetEmail, VerificationView, LoginView, LogoutView,CompletePasswordReset
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
urlpatterns=[
path('validate-username',csrf_exempt(UsernameValidationview.as_view()),name='validate-username'),
path('validate-email',csrf_exempt(EmailValidationview.as_view()),name='validate-email'),
path('register', csrf_exempt(registerationview.as_view()), name='register'),
path('activate/<uidb64>/<token>', VerificationView.as_view(),name='activate'),
path('login', LoginView.as_view(), name='login'),
path('logout',LogoutView.as_view(), name='logout'),
path('request-reset-link', RequestPasswordResetEmail.as_view(), name='request-password'),
path('set-new-password/<uidb64>/<token>', CompletePasswordReset.as_view(),name='reset-user-password'),
path('set-newpassword', registerationview.as_view(), name='set-newpassword'),

]




