from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, Group
from http import HTTPStatus


User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user1 = User.objects.create(username='user1')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author.force_login(self.user1)

    def test_status_guest_found(self):
        reverse_names = {
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            reverse('posts:post_create'),
        }
        for reverse_name in reverse_names:
            with self.subTest(reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_status_guest_ok(self):
        reverse_names = {
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
            reverse('posts:profile', kwargs={'username': self.post.author}),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('about:tech'),
            reverse('about:author'),
            reverse('posts:index'),
        }
        for reverse_name in reverse_names:
            with self.subTest(reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_status(self):
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_status_not_author(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_status_author(self):
        response = self.authorized_client_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_noname_status(self):
        response = self.guest_client.get('/noname/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user1 = User.objects.create(username='user1')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author.force_login(self.user1)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
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
        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

        templates_url_names = {
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_post_not_authorized(self):
        response = self.guest_client.get(reverse('posts:post_create'))
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_create_post_not_authorized(self):
        response = self.guest_client.get(reverse('posts:post_create'))
        self.assertRedirects(
            response, f"{reverse('users:login')}?next=/create/"
        )

    def test_edit_post_not_authorized(self):
        response = self.guest_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertRedirects(
            response,
            f"{reverse('users:login')}?next=/posts/{self.post.id}/edit/"
        )
