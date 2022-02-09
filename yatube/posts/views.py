from django.core.paginator import Paginator

from django.contrib.auth.decorators import login_required

from django.shortcuts import get_object_or_404, render, redirect

from .forms import PostForm, CommentForm

from .models import Follow, Post, Group, User


QUANTITY_POSTS = 10


def index(request):
    posts = Post.objects.select_related('group', 'author')
    title = 'Последние обновления на сайте'
    paginator = Paginator(posts, QUANTITY_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'title': title,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.order_by()
    title = 'Записи сообщества ' + group.title
    paginator = Paginator(posts, QUANTITY_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'group': group,
        'title': title,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    title = 'Профайл пользователя ' + username
    user = request.user
    author = get_object_or_404(User, username=username)
    if (user.is_authenticated and author != user and Follow.objects.filter(
        author=author,
        user=user
    ).exists()):
        following = True
    else:
        following = False
    posts = author.posts.all()
    paginator = Paginator(posts, QUANTITY_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'title': title,
        'page_obj': page_obj,
        'author': author,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comment_form = CommentForm(request.POST or None)
    comments = post.comments.all()
    title = 'Пост ' + post.text[0:30] + '...'
    context = {
        'post': post,
        'title': title,
        'comments': comments,
        'form': comment_form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=post.author)
    form = PostForm()
    context = {
        'form': form,
        'is_edit': False,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST, 
        instance=post,
        files=request.FILES or None
    )
    if form.is_valid():
        post.author = request.user
        post = form.save(commit=False)
        post.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, 'posts/create_post.html', 
                  {'form': form, 'is_edit': True}) 


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    follow = user.follower.all()
    author = User.objects.filter(following__in=follow).all()
    posts = Post.objects.filter(author__in=author).all()
    # posts = follow.author.posts.all()
    paginator = Paginator(posts, QUANTITY_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = 'Подписки пользователя '
    context = {
        'page_obj': page_obj,
        'title': title,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора"""
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(
        user=request.user,
        author=author
    )
    if (request.user != author and not follow.exists()):
        Follow.objects.create(
            user=request.user,
            author=author,
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(
        user=request.user,
        author=author
    )
    if request.user != author and follow.exists():
        Follow.objects.filter(
            user=request.user,
            author=author,
        ).delete()
    return redirect('posts:profile', username=username)
