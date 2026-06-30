from .models import Like, Repost, Bookmark


def attach_comment_threads(posts):
    for post in posts:
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


def attach_engagement_state(posts, user):
    if not user.is_authenticated:
        for post in posts:
            post.user_has_liked = False
            post.user_has_reposted = False
            post.user_has_bookmarked = False
        return

    liked_ids = set(Like.objects.filter(user=user).values_list('post_id', flat=True))
    reposted_ids = set(Repost.objects.filter(user=user).values_list('post_id', flat=True))
    bookmarked_ids = set(Bookmark.objects.filter(user=user).values_list('post_id', flat=True))

    for post in posts:
        post.user_has_liked = post.id in liked_ids
        post.user_has_reposted = post.id in reposted_ids
        post.user_has_bookmarked = post.id in bookmarked_ids