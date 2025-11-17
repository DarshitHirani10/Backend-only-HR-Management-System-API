from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from django.utils import timezone
import logging
from accounts.serializers import UserSerializer
from accounts.models import Role, Department, Designation
from accounts.utils import create_otp_payload, send_otp_email
from notifications.utils import notify_password_reset, notify_user_deleted, notify_profile_updated

logger = logging.getLogger(__name__)
User = get_user_model()


def get_access_token_for_user(user):
    return str(AccessToken.for_user(user))


class RegisterUserView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            current = request.user
            if not current.role or current.role.name != "admin":
                return Response({"msg": "Access denied. Only Admin can register users."},status=status.HTTP_403_FORBIDDEN)
            data = request.data or {}
            email = data.get("email")
            username = data.get("username")
            password = data.get("password")
            confirm_password = data.get("confirm_password")
            first_name = data.get("first_name", "")
            last_name = data.get("last_name", "")
            role_name = data.get("role")
            dept_name = data.get("department")
            desg_name = data.get("designation")
            bio = data.get("bio")
            phone = data.get("phone")
            address = data.get("address")

            if not email or not username or not password or not confirm_password:
                return Response({"msg": "email, username, password and confirm-password required"},status=status.HTTP_400_BAD_REQUEST)
            if password != confirm_password:
                return Response({"msg": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(email=email).exists():
                return Response({"msg": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(username=username).exists():
                return Response({"msg": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

            role = Role.objects.filter(name=role_name).first() if role_name else None
            department = Department.objects.filter(name=dept_name).first() if dept_name else None
            designation = Designation.objects.filter(name=desg_name).first() if desg_name else None

            user = User.objects.create_user(
                email=email,
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role,
                department=department,
                designation=designation,
                bio=bio,
                phone=phone,
                address=address
            )
            return Response({"user": UserSerializer(user).data, "msg": f"User {username} created successfully"}, status=status.HTTP_201_CREATED)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        try:
            data = request.data or {}
            email = data.get("email")
            password = data.get("password")
            if not email or not password:
                return Response({"msg": "email and password required"}, status=status.HTTP_400_BAD_REQUEST)
            user = authenticate(email=email, password=password)
            if not user:
                return Response({"msg": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])
            access_token = get_access_token_for_user(user)
            return Response({
                "msg": "Login successful", 
                "token": access_token, 
                "user": UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            return Response({"msg": "Logged out successfully"}, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


OTP_STORE = {}  # { email: {"code": "123456", "expires_at": datetime} }

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        try:
            data = request.data or {}
            email = data.get("email")
            if not email:
                return Response({"msg": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.filter(email=email).first()
            if not user:
                return Response({"msg": "No user with this email"}, status=status.HTTP_404_NOT_FOUND)
            otp_payload = create_otp_payload(email, minutes_valid=5)
            OTP_STORE[email] = {"code": otp_payload["code"], "expires_at": otp_payload["expires_at"]}
            try:
                send_otp_email(email, otp_payload["code"])
            except Exception as mail_exc:
                return Response({"msg": "Failed to send OTP email", "error": str(mail_exc)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({"msg": "OTP sent to registered email"}, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class VerifyOtpView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        try:
            data = request.data or {}
            email = data.get("email")
            code = data.get("code")
            if not email or not code:
                return Response({"msg": "email and code required"}, status=status.HTTP_400_BAD_REQUEST)
            stored = OTP_STORE.get(email)
            if not stored:
                return Response({"msg": "No OTP requested for this email"}, status=status.HTTP_400_BAD_REQUEST)
            if timezone.now() > stored["expires_at"]:
                del OTP_STORE[email]
                return Response({"msg": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)
            if str(stored["code"]) != str(code):
                return Response({"msg": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
            stored["verified"] = True
            return Response({"msg": "OTP verified"}, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data or {}
            email = data.get("email")
            new_password = data.get("new_password")
            confirm_password = data.get("confirm_password")

            if not email or not new_password or not confirm_password:
                return Response({"msg": "email, new-password, confirm-password required"}, status=status.HTTP_400_BAD_REQUEST)
            stored = OTP_STORE.get(email)
            if not stored:
                return Response({"msg": "No OTP requested for this email"}, status=status.HTTP_400_BAD_REQUEST)
            if not stored.get("verified"):
                return Response({"msg": "OTP not verified"}, status=status.HTTP_400_BAD_REQUEST)
            if timezone.now() > stored["expires_at"]:
                del OTP_STORE[email]
                return Response({"msg": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)
            if new_password != confirm_password:
                return Response({"msg": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.filter(email=email).first()
            if not user:
                return Response({"msg": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            user.set_password(new_password)
            user.save()
            try:
                notify_password_reset(user, None)
                logger.info(f"Password reset notification sent to {user.username}")
            except Exception as notif_error:
                logger.exception(f"Failed to send notification: {notif_error}")
            del OTP_STORE[email]
            return Response({"msg": "Password reset successfully"}, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)



class UserView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            user = request.user
            qs = User.objects.none()
            if user.role and user.role.name == "admin":
                qs = User.objects.all()
            elif user.role and user.role.name == "senior":
                if user.department:
                    qs = User.objects.filter(department=user.department).exclude(id=user.id)
                else:
                    qs = User.objects.none()
            elif user.role and user.role.name == "junior":
                if user.department:
                    qs = User.objects.filter(department=user.department, role__name="intern")
            elif user.role and user.role.name == "intern":
                qs = User.objects.filter(id=user.id)
            data = UserSerializer(qs, many=True).data
            return Response({"users": data}, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, id):
        try:
            user = request.user
            target_user = User.objects.filter(id=id).first()
            if not target_user:
                return Response({"msg": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            if user.role.name == "admin":
                if target_user.id == user.id:
                    return Response({"msg": "Admin cannot delete themselves"}, status=status.HTTP_403_FORBIDDEN)
                try:
                    notify_user_deleted(target_user, user)
                    logger.info(f"User deletion notification sent to {target_user.username}")
                except Exception as notif_error:
                    logger.exception(f"Failed to send deletion notification: {notif_error}")
                
                target_user.delete()
                return Response({"msg": f"User '{target_user.username}' deleted successfully by Admin"}, status=status.HTTP_200_OK)
            elif user.role.name == "senior":
                if not target_user.department or target_user.department != user.department:
                    return Response({"msg": "You can only delete users in your department"}, status=status.HTTP_403_FORBIDDEN)
                if target_user.role.name in ["junior", "intern"]:
                    try:
                        notify_user_deleted(target_user, user)
                        logger.info(f"User deletion notification sent to {target_user.username}")
                    except Exception as notif_error:
                        logger.exception(f"Failed to send deletion notification: {notif_error}")
                    
                    target_user.delete()
                    return Response({"msg": f"User '{target_user.username}' deleted successfully by Senior"}, status=status.HTTP_200_OK)
                else:
                    return Response({"msg": "You can only delete juniors or interns"}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({"msg": "You do not have permission to delete users"}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"msg": f"Error deleting user: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class ProfileViewUpdate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id=None):
        current = request.user
        target = User.objects.filter(id=user_id).first() if user_id else current
        if not target:
            return Response({"msg": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if current.role and current.role.name == "admin":
            pass
        elif current.role and current.role.name == "senior":
            if target.department != current.department:
                return Response({"msg": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
        elif target.id != current.id:
            return Response({"msg": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
        return Response(UserSerializer(target).data, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        current_user = request.user  # who is making the request
        user_id = kwargs.get('id')   # whose profile to update
        data = request.data          # data sent from frontend
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        if current_user.role and current_user.role == "admin":
            for key, value in data.items():
                if key == "role":
                    role_obj = Role.objects.filter(name=value).first()
                    if role_obj:
                        user.role = role_obj
                elif key == "department":
                    dept_obj = Department.objects.filter(name=value).first()
                    if dept_obj:
                        user.department = dept_obj
                elif key == "designation":
                    desig_obj = Designation.objects.filter(name=value).first()
                    if desig_obj:
                        user.designation = desig_obj
                elif hasattr(user, key):
                    setattr(user, key, value)
        else:
            allowed_fields = ['first_name', 'last_name', 'bio', 'phone', 'address']
            for key, value in data.items():
                if key in allowed_fields and hasattr(user, key):
                    setattr(user, key, value)
        user.save()
        
        try:
            notify_profile_updated(user, current_user)
            logger.info(f"Profile update notification sent to {user.username}")
        except Exception as notif_error:
            logger.exception(f"Failed to send profile update notification: {notif_error}")
        
        serializer = UserSerializer(user)
        return Response(serializer.data, status=200)


