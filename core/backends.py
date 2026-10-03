from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

class EmailOrPhoneBackend(ModelBackend):
    """Log in with email or phone number (phone stored on Profile)."""
    def authenticate(self, request, username=None, password=None, **kw):
        User = get_user_model()
        user = User.objects.filter(Q(email__iexact=username) | Q(username=username) | Q(profile__phone=username)).first()
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
