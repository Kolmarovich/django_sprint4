from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, reverse
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from blog.models import Category, Comment, Post, User
from .forms import CommentForm, PostForm, UserForm


class PaginatorMixin:
    '''Постраничный вывод для страницы категории.'''
    def my_pagination(self, context, per_page=10):
        paginator = Paginator(context['post_list'], per_page)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        page_obj = paginator.get_page(1)
        context['page_obj'] = page_obj
        return context


class IndexListView(ListView):
    '''Главная страница.'''
    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10
    queryset = Post.objects.select_related(
        'location', 'author', 'category'
    ).filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    ).order_by('-pub_date').annotate(comment_count=Count('post_comments'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_count'] = Comment.objects.annotate(Count('id'))
        return context


class PostDetailView(DetailView):
    '''Страница отдельного поста.'''
    model = Post
    template_name = 'blog/detail.html'

    def dispatch(self, request, *args, **kwargs):
        if (
            not self.get_object().is_published
            and (self.get_object().author != request.user)

        ):
            raise Http404('Page was not found')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.post_comments.select_related(
                'author'
            ).order_by('created_at')
        )
        return context


class CategoryListView(PaginatorMixin, ListView):
    '''Страница отдельной категории.'''
    model = Category
    template_name = 'blog/category.html'

    def dispatch(self, request, *args, **kwargs):
        self.post_list = Post.objects.filter(
            category__slug=kwargs['category_slug'],
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now(),
        ).order_by('-pub_date').annotate(comment_count=Count("post_comments"))

        self.category = get_object_or_404(
            Category.objects
            .values('title', 'description'),
            slug=kwargs['category_slug'],
            is_published=True
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post_list'] = self.post_list
        context['category'] = self.category
        return self.my_pagination(context)


class ProfileListView(ListView):
    '''Страница профиля пользователя.'''
    model = User
    template_name = 'blog/profile.html'
    ordering = '-pub_date'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = User.objects.get(username=self.kwargs['username'])
        return context

    def get_queryset(self):
        self.author = get_object_or_404(User, username=self.kwargs['username'])
        if self.request.user.username == self.kwargs['username']:
            return Post.objects.select_related(
                'location', 'category', 'author'
            ).filter(
                author=self.author
            ).order_by('-pub_date').annotate(
                comment_count=Count("post_comments"))
        return Post.objects.select_related(
            'location', 'category', 'author'
        ).filter(
            author=self.author,
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True,
        ).order_by('-pub_date').annotate(comment_count=Count("post_comments"))


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    '''редактирование страницы профиля пользователя.'''
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.kwargs['username']},
        )


class PostCreateView(LoginRequiredMixin, CreateView):
    '''Страница написания поста.'''
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        slug = self.request.user.username
        return reverse('blog:profile', kwargs={'username': slug})

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UpdateView):
    '''Страница изменения поста.'''
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'pk'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'pk': self.kwargs['pk']},
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.kwargs['pk']
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=self.kwargs['pk'])
        if instance.author != request.user:
            return redirect('blog:post_detail', self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    '''Страница удаления поста.'''
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != self.request.user:
            return redirect('blog:post_detail', post.pk)
        return super().dispatch(request, *args, **kwargs)


class CommentCreateView(LoginRequiredMixin, CreateView):
    '''Страница написания комментария.'''
    model = Comment
    form_class = CommentForm
    queryset = Comment.objects
    pk_url_kwarg = 'pk'
    posts = None

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'pk': self.posts.pk},
        )

    def dispatch(self, request, *args, **kwargs):
        self.posts = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.posts
        return super().form_valid(form)


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    '''Страница обновления комментария.'''
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=kwargs['comment_id'])
        if instance.author != request.user:
            return redirect('blog:post_detail', instance.post_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'pk': self.kwargs['pk']},
        )


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    '''Страница удаления комментария.'''
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=kwargs['comment_id'])
        if instance.author != request.user:
            return redirect('blog:post_detail', instance.post_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'pk': self.kwargs['pk']},
        )
