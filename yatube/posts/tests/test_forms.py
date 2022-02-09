import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm, CommentForm
from posts.models import Post, Group, User, Comment
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user1 = User.objects.create(username='Yana')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.group1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_slug_1',
            description='Тестовое описание 1'
        )
        cls.image = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded_img = SimpleUploadedFile(
            name='test.jpg',
            content=cls.image,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            pub_date='28.01.22',
            image=cls.uploaded_img,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author.force_login(self.user1)

    def test_create_post(self):
        post_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст поста',
            'image': self.image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': self.post.author}
            )
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст поста',
                author=PostFormTests.user,
                group=PostFormTests.group,
                image=self.post.image
            ).exists()
        )

    def test_post_edit(self):
        form_data = {
            'text': 'Тестовый текст новый',
            'group': self.group1.id,
            'image': self.image
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
            id=self.post.id,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст новый',
                id=self.post.id,
                group=PostFormTests.group1,
                image=self.post.image
            ).exists()
        )


class TestCommentForm(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create(username="Yana")
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста',
        )
        cls.form = CommentForm()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_add_comment(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст comment'
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True,
            id=self.post.pk
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertTrue(
            Post.objects.filter(
                id=self.post.pk,
                text='Тестовый текст поста'
            ).exists()
        )
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый текст comment'
            ).exists()
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
