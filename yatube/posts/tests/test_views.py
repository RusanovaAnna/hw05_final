from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Post, Group, Follow
from posts.forms import PostForm
from posts.views import QUANTITY_POSTS

User = get_user_model()

SIZE = 13


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.user1 = User.objects.create(username='Yana')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        image = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded_img = SimpleUploadedFile(
            name='test.jpg',
            content=image,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded_img,
        )
        cls.post1 = Post.objects.create(
            text='Тестовый текст 1',
            author=cls.user1,
            group=cls.group,
        )
        cls.form = PostForm

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author.force_login(self.user1)

    def test_views_uses_correct_template(self):
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.post.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_views_uses_correct_template_create(self):
        response = self.authorized_client_author.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post1.id})
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_index_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        for post in Post.objects.all():
            page_obj = response.context['page_obj']
            self.assertIn(post, page_obj)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(
            response.context.get('group').title, 'Тестовая группа'
        )
        self.assertEqual(response.context.get('group').slug, 'test_slug')

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        for post in Post.objects.all():
            if 'author_id' == self.user:
                response = self.authorized_client.get(reverse(
                    'posts:profile', kwargs={'username': 'auth'}
                ))
                page_obj = response.context['page_obj']
                self.assertIn(post, page_obj)

    def test_post_edit_pages_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post1.id})
        )
        form_fields = {
            'group': forms.models.ModelChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_create_pages_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'group': forms.models.ModelChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_cache_index_page_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        content = response.content
        post_id = PostViewsTests.post.id
        instance = Post.objects.get(pk=post_id)
        instance.delete()
        new_response = self.authorized_client.get(reverse('posts:index'))
        new_content = new_response.content
        self.assertEqual(content, new_content)
        cache.clear()
        new_response_new = self.authorized_client.get(reverse('posts:index'))
        new_content_new = new_response_new.content
        self.assertNotEqual(content, new_content_new)

    def test_user_can_follow(self):
        author = self.user
        user = self.user1
        #response = self.authorized_client.get(
            #reverse(
                #'posts:profile_follow', kwargs={'username': author.username}
           #)
        #)
        self.assertTrue(
            Follow.objects.filter(
                author=author,
                user=user
            ).exists())


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Yana')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        Post.objects.bulk_create(
            [
                Post(
                    author=cls.user,
                    text='Текст',
                    group=cls.group)
                for i in range(SIZE)
            ]
        )

    def setUp(self):
        self.guest_client = Client()

    def test_paginator_first_and_second_page(self):
        reverse_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user}),
        )
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), QUANTITY_POSTS
                )
                POST = SIZE - QUANTITY_POSTS
                response = self.guest_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), POST)
