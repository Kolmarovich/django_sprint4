from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, reverse
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.urls import reverse_lazy

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
    ).order_by('-pub_date').annotate(comment_count=Count('comments'))


class PostDetailView(DetailView):
    '''Страница отдельного поста.'''

    model = Post
    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        post_id = self.kwargs.get('pk')
        user = self.request.user
        queryset = queryset or self.get_queryset()
        if user.is_authenticated:
            post = queryset.filter(
                Q(id=post_id) &
                (Q(author=user) | Q(is_published=True))
            ).select_related('author').first()
        else:
            post = queryset.filter(
                Q(id=post_id) & Q(is_published=True)
            ).select_related('author').first()
        if not post:
            raise Http404('Page was not found')
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments
            .select_related('author')
            .order_by('created_at')
        )
        return context


class CategoryListView(PaginatorMixin, ListView):
    '''Страница отдельной категории.'''

    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'post_list'

    def get_queryset(self):
        category_slug = self.kwargs['category_slug']
        return Post.objects.filter(
            category__slug=category_slug,
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        ).order_by('-pub_date').annotate(comment_count=Count('comments'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs['category_slug']
        category = get_object_or_404(
            Category.objects.values('title', 'description'),
            slug=category_slug,
            is_published=True
        )
        context['category'] = category
        return self.my_pagination(context)


class ProfileListView(PaginatorMixin, ListView):
    '''Страница профиля пользователя.'''

    template_name = 'blog/profile.html'
    context_object_name = 'post_list'
    ordering = '-pub_date'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(User, username=self.author)
        return self.my_pagination(context)

    def get_queryset(self):
        self.author = get_object_or_404(User, username=self.kwargs['username'])
        if self.request.user.username == self.kwargs['username']:
            return Post.objects.select_related(
                'location', 'category', 'author'
            ).filter(
                author=self.author
            ).order_by('-pub_date').annotate(
                comment_count=Count('comments')
            )
        return Post.objects.select_related(
            'location', 'category', 'author'
        ).filter(
            author=self.author,
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True,
        ).order_by('-pub_date').annotate(comment_count=Count('comments'))


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

    def dispatch(self, request, *args, **kwargs):
        instance = self.get_object()
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
        if self.get_object().author != self.request.user:
            return redirect('blog:post_detail', self.get_object().pk)
        return super().dispatch(request, *args, **kwargs)


class CommentCreateView(LoginRequiredMixin, CreateView):
    '''Страница написания комментария.'''

    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'pk'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'pk': self.object.post.pk},
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['pk'])
        return super().form_valid(form)


class CommentPermissionMixin(LoginRequiredMixin):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return redirect('blog:post_detail', instance.post_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'pk': self.kwargs['pk']},
        )


class CommentUpdateView(CommentPermissionMixin, UpdateView):
    '''Страница обновления комментария.'''


class CommentDeleteView(CommentPermissionMixin, DeleteView):
    '''Страница удаления комментария.'''
