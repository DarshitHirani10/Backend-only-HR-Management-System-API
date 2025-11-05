import random
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

def generate_otp(length=6):
    start = 10**(length-1)
    end = (10**length)-1
    return str(random.randint(start, end))

def create_otp_payload(email, minutes_valid=5):
    code = generate_otp()
    expires_at = timezone.now() + timedelta(minutes=minutes_valid)
    return {"email": email, "code": code, "expires_at": expires_at}

def send_otp_email(email, code):
    subject = "HRMS Password Reset OTP"
    message = f"Your OTP for password reset is: {code}. It is valid for a few minutes."
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER)
    send_mail(subject, message, from_email, [email], fail_silently=False)
