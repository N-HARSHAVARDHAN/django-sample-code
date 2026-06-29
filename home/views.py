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

    # --- NEW: figure out what the current user has liked/reposted/bookmarked ---
    liked_ids = set(Like.objects.filter(user=request.user).values_list('post_id', flat=True))
    reposted_ids = set(Repost.objects.filter(user=request.user).values_list('post_id', flat=True))
    bookmarked_ids = set(Bookmark.objects.filter(user=request.user).values_list('post_id', flat=True))

    for item in feed:
        post = item["post"]

        # --- NEW: attach booleans for template ---
        post.user_has_liked = post.id in liked_ids
        post.user_has_reposted = post.id in reposted_ids
        post.user_has_bookmarked = post.id in bookmarked_ids

        all_comments = list(post.comments.all())
        all_comments.sort(key=lambda x: x.created_at)

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

    return render(request, 'homepage.html', {
        'feed': feed,
        'tab': tab
    })