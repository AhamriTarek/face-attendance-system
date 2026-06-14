from django.shortcuts import redirect
from functools import wraps

def professor_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.session.get('role') == 'professor':
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return _wrapped_view

def student_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.session.get('role') == 'student':
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return _wrapped_view

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.session.get('role') == 'admin':
            return view_func(request, *args, **kwargs)
        return redirect('accueil')
    return _wrapped_view

def login_required_custom(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if any role session key exists
        role = request.session.get('role')
        if not role:
            return redirect('/accueil/')
        return view_func(request, *args, **kwargs)
    return wrapper
