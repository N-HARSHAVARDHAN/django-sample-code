from django.shortcuts import render,redirect

# Create your views here.

from django.contrib.auth import authenticate , login , logout 
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import User 
from .models import VerificationRequest
from posts.models import Post,Repost,Like,Bookmark
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
def profile_view(request, username):
    user_profile = get_object_or_404(User, username=username)

    posts = (
        Post.objects
        .filter(user=user_profile)
        .prefetch_related('comments__user')
        .order_by('-created_at')
    )

    reposts = (
        Repost.objects
        .filter(user=user_profile)
        .select_related("post", "post__user")
        .order_by("-created_at")
    )

    for post in posts:
        all_comments = list(post.comments.all().order_by('created_at'))

        comment_map = {c.id: c for c in all_comments}
        children_map = {}
        top_comments = []

        for c in all_comments:
            c.reply_to = comment_map.get(c.parent_id) if c.parent_id else None

            if c.parent_id is None:
                top_comments.append(c)
            else:
                children_map.setdefault(c.parent_id, []).append(c)

        def collect_descendants(comment_id):
            result = []

            for child in children_map.get(comment_id, []):
                result.append(child)
                result.extend(collect_descendants(child.id))

            return result

        for c in top_comments:
            descendants = collect_descendants(c.id)
            descendants.sort(key=lambda x: x.created_at)
            c.ui_replies = descendants

        post.top_comments = top_comments

    # -------------------------------
    # Build profile feed
    # -------------------------------

    profile_feed = []

    for post in posts:
        profile_feed.append({
            "type": "post",
            "created_at": post.created_at,
            "post": post,
        })

    for repost in reposts:
        profile_feed.append({
            "type": "repost",
            "created_at": repost.created_at,
            "post": repost.post,
            "reposted_by": repost.user,
        })

    profile_feed.sort(
        key=lambda item: item["created_at"],
        reverse=True
    )

    # --- NEW: attach like/repost/bookmark state for current viewer ---
    liked_ids = set(Like.objects.filter(user=request.user).values_list('post_id', flat=True))
    reposted_ids = set(Repost.objects.filter(user=request.user).values_list('post_id', flat=True))
    bookmarked_ids = set(Bookmark.objects.filter(user=request.user).values_list('post_id', flat=True))

    for item in profile_feed:
        post = item["post"]
        post.user_has_liked = post.id in liked_ids
        post.user_has_reposted = post.id in reposted_ids
        post.user_has_bookmarked = post.id in bookmarked_ids

    followers_count = user_profile.followers.count()
    following_count = user_profile.following.count()

    is_following = request.user.following.filter(
        id=user_profile.id
    ).exists()

    return render(request, 'profile.html', {
        'user_profile': user_profile,
        'posts': posts,
        'profile_feed': profile_feed,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,
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

@login_required
def follow_user(request,user_id):
    user_to_follow = get_object_or_404(User,id = user_id)
    if request.user != user_to_follow:
        if user_to_follow in request.user.following.all():
            request.user.following.remove(user_to_follow)
        else:
            request.user.following.add(user_to_follow)
    return redirect('accounts:profile' , username = user_to_follow.username)

@login_required
def followers_list(request,username):
    user_profile = get_object_or_404(User,username=username)
    followers = user_profile.followers.all()

    return render(request,'follow_list.html',{
        'user_profile':user_profile,
        'users':followers,
        'title':'followers',
    })

@login_required
def following_list(request,username):
    user_profile = get_object_or_404(User,username=username)
    following= user_profile.following.all()
    return render(request,'follow_list.html',{
        'user_profile':user_profile,
        'users':following,
        'title':'following',
    })

@login_required
def people(request):
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'people.html', {'users': users})


@login_required
def request_verification(request):
    user = request.user

    if user.verification_status in ['none', 'rejected']:
        user.verification_status = 'pending'
        user.save()

    return redirect('accounts:profile', username=user.username)

from django.shortcuts import render
from django.db.models import Q
from .models import User

def search_page(request):
    query = request.GET.get('q', '')
    users = []

    if query:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(bio__icontains=query)
        )

    return render(request, 'search.html', {
        'users': users,
        'query': query
    })