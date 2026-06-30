from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import Post, Like, Comment, Repost, Bookmark
from .utils import attach_comment_threads, attach_engagement_state
# Create your views here.

def create_post(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')
        video = request.FILES.get('video')

        Post.objects.create(
            user=request.user,
            content=content,
            image=image,
            video=video
        )

        return redirect('home:homepage')
    return render(request,'create_post.html')

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    like = Like.objects.filter(user=request.user, post=post).first()

    if like:
        like.delete()
        liked = False
    else:
        Like.objects.create(user=request.user, post=post)
        liked = True

    return JsonResponse({
        "liked": liked,
        "count": post.likes.count()
    })

@login_required
def repost_post(request, post_id):

    post = get_object_or_404(Post, id=post_id)

    repost = Repost.objects.filter(
        user=request.user,
        post=post
    ).first()

    if repost:
        repost.delete()
        reposted = False
    else:
        Repost.objects.create(
            user=request.user,
            post=post
        )
        reposted = True

    return JsonResponse({
        "reposted": reposted,
        "count": post.reposts.count()
    })

@login_required
def comment_post(request, post_id):
    if request.method == "POST":

        post = get_object_or_404(Post, id=post_id)

        text = request.POST.get("comment")
        parent_id = request.POST.get("parent_id")

        if text:
            parent = get_object_or_404(Comment, id=parent_id) if parent_id else None

            comment = Comment.objects.create(
                user=request.user,
                post=post,
                text=text,
                parent=parent
            )

            comment.reply_to = parent
            is_reply = parent is not None
            parent_top_id = (parent.parent_id or parent.id) if parent else None

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                html = render_to_string(
                    "comment.html",
                    {
                        "comment": comment,
                        "is_reply": is_reply,
                    },
                    request=request
                )
                return JsonResponse({
                    "success": True,
                    "html": html,
                    "is_reply": is_reply,
                    "parent_top_id": parent_top_id,
                })

    return redirect(request.META.get("HTTP_REFERER", "home:homepage"))
@login_required
def delete_post(request,post_id):
    post = get_object_or_404(Post,id = post_id)

    if request.user!=post.user:
        return redirect('home:homepage')
    post.delete()
    return redirect(request.META.get('HTTP_REFERER','home:homepage'))

@login_required
def delete_comment(request, comment_id):

    if request.method != "POST":
        return JsonResponse({"success": False}, status=405)

    comment = get_object_or_404(
        Comment,
        id=comment_id,
        user=request.user
    )

    comment.delete()

    return JsonResponse({
        "success": True,
        "comment_id": comment_id
    })

@login_required
def edit_comment(request, comment_id):

    if request.method != "POST":
        return JsonResponse({"success": False}, status=405)

    comment = get_object_or_404(
        Comment,
        id=comment_id,
        user=request.user
    )

    text = request.POST.get("text", "").strip()

    if not text:
        return JsonResponse({
            "success": False,
            "error": "Comment cannot be empty."
        })

    comment.text = text
    comment.save()

    return JsonResponse({
        "success": True,
        "text": comment.text
    })


@login_required
def toggle_bookmark(request, post_id):
    post = Post.objects.get(id=post_id)

    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user,
        post=post
    )

    if not created:
        bookmark.delete()
        return JsonResponse({"status": "removed"})

    return JsonResponse({"status": "bookmarked"})



@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # must be owner
    if request.user != post.user:
        return redirect('home:homepage')

    # must be verified
    if request.user.verification_status != "approved":
        return HttpResponseForbidden("Only verified users can edit posts")

    if request.method == "POST":
        content = request.POST.get("content")
        post.content = content
        post.save()
        return redirect('home:homepage')

    return render(request, "edit_post.html", {"post": post})

def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    attach_engagement_state([post], request.user)
    attach_comment_threads([post])
    return render(request, "post_detail.html", {"post": post})


@login_required
def bookmarks(request):
    bookmarks_qs = Bookmark.objects.filter(user=request.user).select_related('post', 'post__user')
    posts = [b.post for b in bookmarks_qs]
    attach_engagement_state(posts, request.user)
    attach_comment_threads(posts)
    return render(request, "bookmarks.html", {"posts": posts})


@login_required
def trending_view(request):
    now = timezone.now()
    last_24_hours = now - timedelta(hours=24)

    posts = Post.objects.filter(
        created_at__gte=last_24_hours
    ).select_related("user").annotate(
        like_count=Count("likes"),
        comment_count=Count("comments"),
    )

    # Python-based scoring (safe)
    for post in posts:
        hours_old = (now - post.created_at).total_seconds() / 3600

        post.trending_score = (
            post.like_count * 3 +
            post.comment_count * 5 -
            hours_old * 0.2
        )

    posts = sorted(posts, key=lambda x: x.trending_score, reverse=True)

    attach_engagement_state(posts, request.user)
    attach_comment_threads(posts)

    return render(request, "trending.html", {"posts": posts})