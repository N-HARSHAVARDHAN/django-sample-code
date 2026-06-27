from django.shortcuts import render

# Create your views here.

from django.shortcuts import render,redirect
from django.contrib.auth import authenticate , login , logout 
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import User 
from posts.models import Post
from datetime import date
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404
def signup_view(request):
    if request.method == 'POST':

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        dob = request.POST.get('dob')

        today = date.today()
        min_date = date(today.year - 120, today.month, today.day) 

        if request.method == 'POST':
            dob = request.POST.get('dob')

            if dob:
                try:
                    dob_parsed = date.fromisoformat(dob)
                except ValueError:
                    messages.error(request, "Invalid date of birth")
                    return redirect('accounts:signup')

                if dob_parsed > today:
                    messages.error(request, "Date of birth cannot be in the future")
                    return redirect('accounts:signup')

                if dob_parsed < min_date:
                    messages.error(request, "Please enter a valid date of birth")
                    return redirect('accounts:signup')
            else:
                messages.error(request, "Date of birth is required")
                return redirect('accounts:signup')

        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('accounts:signup')

        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('accounts:signup')

        try:
            validate_password(password)
        except ValidationError as e:
            messages.error(request, e.messages[0])
            return redirect('accounts:signup')

        
        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            dob=dob,
        )

        messages.success(request, "Account created successfully Please login to continue")
        return redirect('accounts:login')

    return render(request, "signup.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("/home")
        else:
            messages.error(request, "Invalid credentials")
            return redirect("accounts:login")

    return render(request, "login.html")

def logout_view(request):
    logout(request)
    return redirect("home:landingpage")

@login_required
def profile_view(request,username):
    user_profile = get_object_or_404(User,username=username)
    posts = Post.objects.filter(user=user_profile).prefetch_related('comments__user').order_by('-created_at')

    for post in posts:
        comments = list(post.comments.all().order_by('created_at'))

        comment_map = {}
        for c in comments:
            c.children = []
            comment_map[c.id] = c

        top_comments = []

        for c in comments:
            if c.parent_id:
                parent = comment_map.get(c.parent_id)
                if parent:
                    parent.children.append(c)
                else:
                    top_comments.append(c)
            else:
                top_comments.append(c)

        post.top_comments = top_comments

    return render(request,'profile.html',{
        'user_profile':user_profile,
        'posts':posts
    })
@login_required
def edit_profile_view(request):
    if request.method =='POST':
        request.user.first_name =request.POST.get('first_name')
        request.user.bio = request.POST.get('bio')
        request.user.dob = request.POST.get('dob') or None

        if 'profile_pic' in request.FILES:
            request.user.profile_pic = request.FILES['profile_pic']
        if 'banner_pic' in request.FILES:
            request.user.banner_pic = request.FILES['banner_pic']
        
        request.user.save()
        return redirect('accounts:profile',username=request.user.username)

    return render(request ,'edit_profile.html',{
        'user': request.user
    })