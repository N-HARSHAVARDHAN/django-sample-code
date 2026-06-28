from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from posts.models import Post,Comment
# Create your views here.
def landingpage(request):
    return render(request,'landingpage.html')

@login_required
def homepage(request):
    tab = request.GET.get('tab', 'for_you')

    if tab == 'following':
        following_users = request.user.following.all()

        posts = Post.objects.filter(
            user__in=following_users
        )
    else:
        posts = Post.objects.all()

    posts = posts.select_related('user').prefetch_related(
        'comments__user'
    ).order_by('-created_at')

    for post in posts:
        all_comments = list(post.comments.all())
        all_comments.sort(key=lambda x: x.created_at)

        comment_map = {}
        for c in all_comments:
            c.children = []
            comment_map[c.id] = c

        top_comments = []

        for c in all_comments:
            if c.parent_id:
                parent = comment_map.get(c.parent_id)
                if parent:
                    parent.children.append(c)
                else:
                    top_comments.append(c)
            else:
                top_comments.append(c)

        post.top_comments = top_comments

    return render(request, 'homepage.html', {
        'posts': posts,
        'tab': tab
    })
    posts = Post.objects.all().select_related('user').prefetch_related(
        'comments__user'
    ).order_by('-created_at')

    for post in posts:
        all_comments = list(post.comments.all())
        all_comments.sort(key=lambda x: x.created_at)

        comment_map = {}
        for c in all_comments:
            c.children = []
            comment_map[c.id] = c

        top_comments = []

        for c in all_comments:
            if c.parent_id:
                parent = comment_map.get(c.parent_id)
                if parent:
                    parent.children.append(c)
                else:
                    top_comments.append(c)
            else:
                top_comments.append(c)

        post.top_comments = top_comments

    return render(request, 'homepage.html', {'posts': posts})