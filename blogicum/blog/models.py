from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

TRUNCATE_LENGTH = 30
User = get_user_model()


class PublishedModel(models.Model):
    '''Абстрактная модель.'''

    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено'
    )

    class Meta:
        abstract = True


class Location(PublishedModel):
    '''Модель местоположения.'''

    name = models.CharField(
        max_length=256,
        verbose_name='Название места',
    )

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self) -> str:
        return self.name[:TRUNCATE_LENGTH]


class Post(PublishedModel):
    '''Модель постов.'''

    title = models.CharField(max_length=256, verbose_name='Заголовок')
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        help_text=(
            'Если установить дату и время в будущем —'
            ' можно делать отложенные публикации.'
        )
    )
    image = models.ImageField('Фото', upload_to='post_images', blank=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Местоположение',
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True, verbose_name='Категория',
    )

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        default_related_name = 'posts'

    def __str__(self) -> str:
        return self.title[:TRUNCATE_LENGTH]

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.pk})


class Category(PublishedModel):
    '''Модель категории.'''

    title = models.CharField(max_length=256, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    slug = models.SlugField(
        unique=True,
        verbose_name='Идентификатор',
        help_text=('Идентификатор страницы для URL; разрешены символы'
                   ' латиницы, цифры, дефис и подчёркивание.')
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self) -> str:
        return self.title[:TRUNCATE_LENGTH]


class Comment(models.Model):
    '''Модель комментариев.'''

    text = models.TextField(max_length=256, verbose_name='Текст комментария')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Автор Комментария',
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE,
        verbose_name='Пост',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено')

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        default_related_name = 'comments'

    def __str__(self):
        return f'''Комментарий {self.author} к посту "{self.post}"
                   (ID: {self.id}).'''
