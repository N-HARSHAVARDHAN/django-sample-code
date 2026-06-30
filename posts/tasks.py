from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from .models import Post

@shared_task
def calculate_trending_scores():
    last_24_hours = timezone.now() - timedelta(hours=24)

    posts = Post.objects.filter(
        created_at__gte=last_24_hours
    ).annotate(
        like_count=Count("likes"),
        comment_count=Count("comments")
    )

    updated_posts = []

    for post in posts:
        score = (
            post.like_count * 3 +
            post.comment_count * 5
        )

        post.trending_score = score
        updated_posts.append(post)

    Post.objects.bulk_update(updated_posts, ["trending_score"])

    return f"Updated {len(updated_posts)} posts"