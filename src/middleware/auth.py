from functools import wraps
from flask import session, redirect

def login_required(f):
    """
    A decorator to ensure the user is logged in before accessing certain routes.
    If the user is not logged in, they are redirected to /login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function
