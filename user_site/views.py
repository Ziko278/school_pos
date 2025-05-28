from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.urls import reverse

from user_site.models import UserProfileModel


def user_sign_in_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            intended_route = request.POST.get('next')
            if not intended_route:
                intended_route = request.GET.get('next')

            remember_me = request.POST.get('remember_me')
            if not remember_me:
                remember_me = request.GET.get('remember_me')

            if user.is_superuser:
                login(request, user)
                messages.success(request, 'welcome back {}'.format(user.username.title()))
                if remember_me:
                    request.session.set_expiry(3600 * 24 * 30)
                else:
                    request.session.set_expiry(0)
                if intended_route:
                    return redirect(intended_route)
                return redirect(reverse('admin_dashboard'))
            try:
                user_role = UserProfileModel.objects.get(user=user)
            except UserProfileModel.DoesNotExist:
                messages.error(request, 'Unknown Identity, Access Denied')
                return redirect(reverse('login'))

            if user_role.staff:
                login(request, user)
                messages.success(request, 'welcome back {}'.format(user_role.staff))
                if remember_me:
                    request.session.set_expiry(3600 * 24 * 30)
                else:
                    request.session.set_expiry(0)
                if intended_route:
                    return redirect(intended_route)
                return redirect(reverse('admin_dashboard'))

            elif user_role.student:
                login(request, user)
                messages.success(request, 'welcome back {}'.format(user_role.student))
                if remember_me:
                    request.session.set_expiry(3600 * 24 * 30)
                else:
                    request.session.set_expiry(0)

                return redirect(reverse('student_dashboard'))

            elif user_role.parent:
                login(request, user)
                messages.success(request, 'welcome back {}'.format(user_role.parent.surname))
                if remember_me:
                    request.session.set_expiry(3600 * 24 * 30)
                else:
                    request.session.set_expiry(0)

                return redirect(reverse('parent_dashboard'))

            else:
                messages.error(request, 'Unknown Identity, Access Denied')
                return redirect(reverse('login'))
        else:
            messages.error(request, 'Invalid Credentials')
            return redirect(reverse('login'))

    return render(request, 'user_site/sign_in.html')


def user_sign_out_view(request):
    logout(request)
    return redirect(reverse('login'))
