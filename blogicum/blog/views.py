from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, reverse
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from blog.models import Category, Comment, Post, User
from blog.forms import CommentForm, PostForm, UserForm
from blog.mixins import (
    CommentUpdateDeleteMixin, PaginatorMixin,
    PostUpdateDeleteMixin, IndexCategoryProfileMixin
)


class IndexListView(IndexCategoryProfileMixin, ListView):
    '''Главная страница.'''

    template_name = 'blog/index.html'


class CategoryListView(LoginRequiredMixin, IndexCategoryProfileMixin,
                       ListView):
    '''Страница отдельной категории.'''

    template_name = 'blog/category.html'
    context_object_name = 'post_list'

    def get_queryset(self):
        queryset = super().get_queryset()
        category_slug = self.kwargs['category_slug']
        return queryset.filter(
            category__slug=category_slug,
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
        return context


class ProfileListView(IndexCategoryProfileMixin, PaginatorMixin, ListView):
    '''Страница профиля пользователя.'''

    template_name = 'blog/profile.html'
    context_object_name = 'post_list'
    ordering = '-pub_date'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.author
        return self.my_pagination(context)

    def get_queryset(self):
        self.author = get_object_or_404(User, username=self.kwargs['username'])
        queryset = super().get_queryset()
        if self.request.user.username == self.kwargs['username']:
            queryset = queryset.filter(author=self.author)
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
                Q(id=post_id) & (Q(author=user) | Q(is_published=True))
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


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    '''Редактирование страницы профиля пользователя.'''

    model = User
    form_class = UserForm
    template_name = 'blog/user.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_object(self, queryset=None):
        profile_user = super().get_object(queryset)
        if profile_user.username != self.request.user.username:
            raise Http404('Page was not found')
        return profile_user

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


class PostUpdateView(PostUpdateDeleteMixin, UpdateView):
    '''Страница изменения поста.'''


class PostDeleteView(PostUpdateDeleteMixin, DeleteView):
    '''Страница удаления поста.'''

    success_url = reverse_lazy('blog:index')


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


class CommentUpdateView(CommentUpdateDeleteMixin, UpdateView):
    '''Страница обновления комментария.'''


class CommentDeleteView(CommentUpdateDeleteMixin, DeleteView):
    '''Страница удаления комментария.'''
