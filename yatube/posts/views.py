from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


NUM_OF_POSTS = 10


def index(request):
    text = 'Последние обновления на сайте'
    post_list = Post.objects.select_related('author', 'group').all()
    paginator = Paginator(post_list, NUM_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'text': text}
    template = 'posts/index.html'
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(
        Group.objects.prefetch_related("posts"), slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, NUM_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    profile = get_object_or_404(User, username=username)
    post_list = (
        Post.objects.select_related("author")
        .filter(author=profile).all()
    )
    posts_count = post_list.count()
    paginator = Paginator(post_list, NUM_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    """if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=profile).exists()
    else:
        following = False"""
    # Можно такой логикой заменить верхний блок(совет ревьюера)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=profile).exists()
    context = {
        'profile': profile,
        'posts_count': posts_count,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post_list = (
        Post.objects.select_related("author", "group")
        .filter(author=post.author).all()
    )
    posts_count = post_list.count()
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'posts_count': posts_count,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, pk=post_id)
    if post.author == request.user:
        form = PostForm(request.POST or None,
                        files=request.FILES or None, instance=post)
        if form.is_valid():
            post = form.save()
            return redirect('posts:post_detail', post.pk)
        form = PostForm(instance=post)
        return render(request, "posts/create_post.html",
                      {'form': form, "is_edit": is_edit})
    else:
        return redirect('posts:post_detail', post.pk)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post.pk)


@login_required
def follow_index(request):
    post_list = Post.objects.select_related('author').filter(
        author__following__user=request.user)
    paginator = Paginator(post_list, NUM_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if user != author:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect('posts:profile', username=username)
    following = Follow.objects.filter(user=request.user, author=author)
    following.delete()
    return redirect('posts:profile', username=username)
