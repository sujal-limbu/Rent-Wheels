from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import SignupClosedException


class NoSignupFormAdapter(DefaultSocialAccountAdapter):
    def is_auto_signup_allowed(self, request, sociallogin):
        return True

    def is_open_for_signup(self, request, sociallogin):
        return True

    def pre_social_login(self, request, sociallogin):
        # If the social account is already connected, skip
        if sociallogin.is_existing:
            return

        # Try to find an existing user with the same email
        try:
            email = sociallogin.account.extra_data.get('email', '').lower()
            if email:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(email__iexact=email)
                sociallogin.connect(request, user)  # connect Google to existing account
        except User.DoesNotExist:
            pass