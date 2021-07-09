from django.shortcuts import render
from django.template.loader import render_to_string
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.models import User
import json
from validate_email import validate_email
from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import redirect
from django.utils.encoding import force_bytes,force_text,DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .utils import token_generator
from .utils import account_activation_token
from django.contrib import auth
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import  threading





# Create your views here.

class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email=email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send(fail_silently=False)



class UsernameValidationview(View):
    def post(self, request):
        data=json.loads(request.body)
        username=data['username']
        if not str(username).isalnum():
            return JsonResponse({'username_error':'username should only contain alphanumeric characters'},status=400)
        if User.objects.filter(username=username).exists():
            return JsonResponse({'username_error': 'sorry username exists choose another'}, status=400)
        return JsonResponse({'username-valid':True})


class EmailValidationview(View):
    def post(self, request):
        data = json.loads(request.body)
        email = data['email']
        if not validate_email(email):
            return JsonResponse({'email_error': 'invalid email'}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({'email_error': 'email is taken choose another email'}, status=400)
        return JsonResponse({'email-valid': True})






class registerationview(View):
    def get(self, request):
        return render(request, 'authentication/register.html')

    def post(self, request):
        username=request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        context={
            'fieldvalues':request.POST
        }
        if not User.objects.filter(username=username).exists():
            if not User.objects.filter(email=email).exists():
                if len(password)<6:
                    messages.error(request, "password should be atleast 6 character long")
                    return render(request, 'authentication/register.html', context)
                user=User.objects.create_user(username=username, email=email)
                user.set_password(password)
                user.is_active=False;
                user.save()
                current_site=get_current_site(request)
                email_body={
                    'user':user,
                    'domain':current_site.domain,
                    'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                    'token':account_activation_token.make_token(user),
                }


                uidb64=urlsafe_base64_encode(force_bytes(user.pk))
                domain=get_current_site(request).domain
                link= reverse('activate',kwargs={"uidb64":uidb64,"token":token_generator.make_token(user)})
                activate_url="http://"+domain+link
                email_subject='Activate your account'
                email_body='Hello '+user.username+ " use this link to activate your account\n"+activate_url
                email = EmailMessage(
                    email_subject,
                    email_body,
                    'noreply@benitv.com',
                    [email],
                )
                EmailThread(email).start()
                #email.send(fail_silently=False)

                messages.success(request, "Account created successfully")
                return render(request, 'authentication/register.html')

        return render(request, 'authentication/register.html')

class VerificationView(View):
    def get(self, request, uidb64, token):
        try:
            id=force_text(urlsafe_base64_decode(uidb64))
            user=User.objects.get(pk=id)
            if not account_activation_token.check_token(user, token):
                return redirect('login' + '?message='+'user is already activated')
            if user.is_active:
                return redirect('login')
            user.is_active=True
            user.save()
            messages.success(request,'account activated successfully')
            return redirect('login')

        except Exception as ex:
            pass
        return redirect('login')



class LoginView(View):
    def get(self, request):
        return render(request, 'authentication/login.html')
    def post(self, request):
        username=request.POST['username']
        password = request.POST['password']
        if username and password:
            user= auth.authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    auth.login(request,user)
                    messages.success(request,'welcome to your account '+ user.username)
                    return redirect('expenses')
                messages.error(request, 'Account is not active, please check your email')
                return render(request, 'authentication/login.html')
            messages.error(request, 'Invalid username or password')
            return render(request, 'authentication/login.html')
        messages.error(request, 'Please fill all fields!')
        return render(request, 'authentication/login.html')


class LogoutView(View):
    def post(self,request):
        auth.logout(request)
        messages.success(request, 'You have logged out successfully')
        return redirect('login')


class RequestPasswordResetEmail(View):
    def get(self, request):
        return render(request, 'authentication/reset-password.html')
    def post(self, request):
        email = request.POST.get('email')

        context = {
            'values': request.POST
        }
        if not validate_email(email):
            messages.error(request, 'invalid email')
            return render(request, 'authentication/reset-password.html', context)

        current_site = get_current_site(request)
        user=User.objects.filter(email=email)
        if user.exists():
            email_contents = {
                'user': user[0],
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user[0].pk)),
                'token': PasswordResetTokenGenerator().make_token(user[0]),
            }
            link = reverse('reset-user-password', kwargs={
                "uidb64": email_contents['uid'], "token": email_contents['token']})
            email_subject = 'Reset your password'
            reset_url = "http://"+current_site.domain + link
            email = EmailMessage(
                email_subject,
                " Hello, use the link below to reset your password \n" + reset_url,
                'noreply@benitv.com',
                [email],
            )
            EmailThread(email).start()
        messages.success(request, "we've sent a reset link to your email")
        return render(request, 'authentication/reset-password.html')

class CompletePasswordReset(View):
    def get(self, request, uidb64, token):
        context={
         'uidb64':uidb64,
         'token': token
        }
        try:
            user_id = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                messages.info(request, 'Your link is no longer valid, Request for new link!')
                return render(request, 'authentication/reset-password.html')
        except Exception as identifier:
            pass
        return render(request, 'authentication/set-new-password.html', context)

    def post(self, request, uidb64, token):
        context = {
            'uidb64': uidb64,
            'token': token
        }
        password=request.POST['password']
        password2 = request.POST['password2']
        if password!=password2:
            messages.error(request,'password mismatch!')
            return render(request, 'authentication/set-new-password.html', context)

        if len(password)<6:
            messages.error(request,'password is too short!')
            return render(request, 'authentication/set-new-password.html', context)

        try:
            user_id = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
            user.set_password(password)
            user.save()
            messages.success(request, 'password updated successfully!')
            return redirect('login')

        except Exception as identifier:
            messages.info(request, 'we have problem resetting your password')
            return render(request, 'authentication/set-new-password.html', context)

