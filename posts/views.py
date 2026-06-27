from django.shortcuts import render,redirect
from django.shortcuts import get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from .models import Post,Like,Comment
from django.http import JsonResponse
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
def comment_post(request,post_id):
    if request.method =='POST':
        post = get_object_or_404(Post,id = post_id)
        text = request.POST.get('comment')
        parent_id = request.POST.get('parent_id')
        if text:
            Comment.objects.create(
                user = request.user,
                post = post,
                text=text,
                parent_id = parent_id if parent_id else None
            )
    return redirect(request.META.get('HTTP_REFERER','home:homepage'))

@login_required
def delete_post(request,post_id):
    post = get_object_or_404(Post,id = post_id)

    if request.user!=post.user:
        return redirect('home:homepage')
    post.delete()
    return redirect(request.META.get('HTTP_REFERER','home:homepage'))
