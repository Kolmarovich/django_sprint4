from django import forms

from .models import Comment, Post, User


class UserForm(forms.ModelForm):
    '''Модель формы для пользователя.'''

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
        )


class PostForm(forms.ModelForm):
    '''Модель формы для поста.'''

    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local',
                                                   'class': 'form-control'})
        }


class CommentForm(forms.ModelForm):
    '''Модель формы для комментария.'''

    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea({'cols': '22', 'rows': '5'})
        }
