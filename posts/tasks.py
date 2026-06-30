from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from .models import Post

@shared_task
def calculate_trending_scores():
    last_24_hours = timezone.now() - timedelta(hours=24)
    posts = Post.objects.filter(created_at__gte=last_24_hours).annotate(like_count=Count("likes"))
    for post in posts:
        post.trending_score = post.like_count
        post.save(update_fields=["trending_score"])
    Post.objects.filter(created_at__lt=last_24_hours, trending_score__gt=0).update(trending_score=0)
    return f"Updated {posts.count()} posts"