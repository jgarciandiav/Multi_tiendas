from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if not request.session.get('last_activity'):
                request.session['last_activity'] = timezone.now().isoformat()
            else:
                last_activity = timezone.datetime.fromisoformat(request.session['last_activity'])
                if (timezone.now() - last_activity).total_seconds() > 300:
                    messages.info(request, "🔒 Sesión cerrada por inactividad (10 minutos).")
                    from django.contrib.auth import logout
                    logout(request)
                    return redirect('login')
            request.session['last_activity'] = timezone.now().isoformat()
        return self.get_response(request)