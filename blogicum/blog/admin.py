from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Comment, Location, Post


class PostInline(admin.StackedInline):
    model = Post
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = (PostInline,)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'pub_date', 'author', 'is_published'),
        }),
        ('Дополнительная информация', {
            'fields': ('location', 'category', 'image_tag'),
        }),
    )
    readonly_fields = ('created_at', 'image_tag')
    list_display = (
        'title',
        'pub_date',
        'author',
        'location',
        'is_published',
        'created_at',
        'category',
        'image_tag',
    )
    list_editable = (
        'is_published',
        'category'
    )
    search_fields = ('title',)
    list_filter = ('is_published',)
    list_display_links = ('title',)

    def image_tag(self, obj):
        if obj.image:
            return format_html('''<img src="{}" width="100"
                               height="100" />''', obj.image.url)
        else:
            return None

    image_tag.short_description = 'Фото'


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    pass


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    pass
