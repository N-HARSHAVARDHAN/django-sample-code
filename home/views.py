from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from posts.models import Post,Comment,Repost,Like,Bookmark
from itertools import chain
# Create your views here.
def landingpage(request):
    return render(request,'landingpage.html')


@login_required
def homepage(request):
    tab = request.GET.get('tab', 'for_you')

    if tab == 'following':
        following_users = request.user.following.all()
        posts_qs = Post.objects.filter(user__in=following_users)
        reposts_qs = Repost.objects.filter(user__in=following_users)
    else:
        posts_qs = Post.objects.all()
        reposts_qs = Repost.objects.all()

    posts_qs = posts_qs.select_related('user')
    reposts_qs = reposts_qs.select_related('user', 'post')

    feed = sorted(
        chain(
            [{"type": "post", "post": p} for p in posts_qs],
            [{"type": "repost", "post": r.post, "reposted_by": r.user, "created_at": r.created_at}
             for r in reposts_qs]
        ),
        key=lambda x: x["post"].created_at,
        reverse=True
    )

    liked_ids = set(Like.objects.filter(user=request.user).values_list('post_id', flat=True))
    reposted_ids = set(Repost.objects.filter(user=request.user).values_list('post_id', flat=True))
    bookmarked_ids = set(Bookmark.objects.filter(user=request.user).values_list('post_id', flat=True))

    for item in feed:
        post = item["post"]

        post.user_has_liked = post.id in liked_ids
        post.user_has_reposted = post.id in reposted_ids
        post.user_has_bookmarked = post.id in bookmarked_ids

        all_comments = list(post.comments.select_related('user').all())
        comment_map = {c.id: c for c in all_comments}

        # 'direct_replies' -- not 'replies', since that name collides with
        # the real reverse FK related_name on the Comment model
        for c in all_comments:
            c.direct_replies = []

        for c in all_comments:
            c.reply_to = comment_map.get(c.parent_id) if c.parent_id else None
            if c.parent_id:
                parent = comment_map.get(c.parent_id)
                if parent:
                    parent.direct_replies.append(c)

        for c in all_comments:
            c.direct_replies.sort(key=lambda x: x.created_at)

        top_comments = [c for c in all_comments if c.parent_id is None]
        top_comments.sort(key=lambda x: x.created_at)

        post.top_comments = top_comments

    return render(request, 'homepage.html', {
        'feed': feed,
        'tab': tab
    })