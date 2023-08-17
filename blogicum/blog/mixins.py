from django.core.paginator import Paginator
from django.shortcuts import redirect, reverse
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count

from blog.models import Comment, Post
from blog.forms import CommentForm, PostForm


class PaginatorMixin:
    '''Постраничный вывод для страницы категории.'''

    def my_pagination(self, context, per_page=10):
        paginator = Paginator(context['post_list'], per_page)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        page_obj = paginator.get_page(1)
        context['page_obj'] = page_obj
        return context


class IndexCategoryProfileMixin():

    model = Post
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True,
        ).order_by('-pub_date').annotate(comment_count=Count('comments'))
        return queryset


class CommentUpdateDeleteMixin(LoginRequiredMixin):
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


class PostUpdateDeleteMixin(LoginRequiredMixin):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return redirect('blog:post_detail', self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)
