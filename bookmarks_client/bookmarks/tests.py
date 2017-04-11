# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from random import randrange
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from httpretty import httpretty
from bookmarks_client.bookmarks.client import BookmarkClient


class MockAPIMixin(object):
    def get_fake_bookmark(self, quantity=1):
        _id = randrange(1, 1000)
        data = {
            "id": _id,
            "title": "Bookmark #%d" % _id,
            "url": "http://foos.bar/%d" % _id,
            "created_at": "2017-04-09T07:34:02.369Z",
            "updated_at": "2017-04-09T07:34:02.369Z",
            "user_id": 1
        }
        if quantity == 1:
            return data
        else:
            bookmarks = []
            for _ in range(quantity):
                bookmarks.append(self.get_fake_bookmark())
            return bookmarks

    def mock_api_verify_headers(self, headers, ignore_content_type=False):
        content_type = headers.get('content-type')
        authorization = headers.get('authorization')
        return (ignore_content_type or content_type == 'application/json') and 'JWT ' in authorization

    def mock_api_content_get_bookmarks(self, request, uri, headers):
        try:
            if self.mock_api_verify_headers(request.headers.dict, ignore_content_type=True):
                bookmarks = self.get_fake_bookmark(quantity=randrange(3, 5))
                headers['content-type'] = 'application/json'
                return 200, headers, json.dumps(bookmarks)
        except KeyError:  # Quando não informa title ou url
            return 400, headers, ''
        return 400, headers, ''

    def mock_api_content_create_or_update_bookmark(self, request, uri, headers):
        data = request.parsed_body
        try:
            if self.mock_api_verify_headers(request.headers.dict) and data['title'] and data['url']:
                return 200, headers, ''
        except KeyError:  # Quando não informa title ou url
            return 400, headers, ''
        return 400, headers, ''

    def mock_api_content_delete_bookmark(self, request, uri, headers):
        id_param = uri.split('/')[-1]
        try:
            _id = int(id_param)
            # Responde sim para as requisições com token e com id par
            if self.mock_api_verify_headers(request.headers.dict, ignore_content_type=True) and _id % 2 == 0:
                return 204, headers, ''
        except ValueError:
            return 400, headers, ''
        return 400, headers, ''

    def mock_api_login_or_create_user(self, request, uri, headers):
        # Apenas retorna login com sucesso do usuário test@example.com com a senha 123456
        data = request.parsed_body
        try:
            email = data['email']
            password = data['password']
            if email == 'test@example.com' and password == '123456':
                return 200, headers, '{"token": "FAKE_TOKEN"}'
        except:  # Quando não informa title ou url
            return 400, headers, ''
        return 400, headers, ''


class HomeViewTest(TestCase):
    def setUp(self):
        self.url = reverse('home')

    def test_home_status(self):
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 200)

    def test_home_template(self):
        response = self.client.get(self.url)
        self.assertEquals(response.template_name, ['home.html'])

    def test_home_has_bootstrap(self):
        response = self.client.get(self.url)
        html = response.content.decode('utf-8')
        self.assertIn('bootstrap.min.css', html)
        self.assertIn('bootstrap.min.js', html)


class LogoutViewTest(TestCase):
    def setUp(self):
        self.url = reverse('logout')

    def test_redirect_to_home(self):
        expected_url = reverse('home')
        response = self.client.get(self.url)
        self.assertRedirects(response, expected_url)

    def test_clear_session(self):
        fake_value = 'asdfasdfasdfasdf'
        s = self.client.session
        s["user"] = fake_value
        s.save()
        # Certifica que a session está "setada"
        self.assertEquals(self.client.session['user'], fake_value)
        self.client.get(self.url)
        # Certifica que a session está limpa
        self.assertEquals(self.client.session['user'], '')


class BookmarkClientTest(MockAPIMixin, TestCase):
    def setUp(self):
        self.token = 'asdfasdfasdf'
        self.url = 'http://domain.com'
        with self.settings(URL_API=self.url):
            self.bookmark_client = BookmarkClient(self.token)

    def test_url_api(self):
        new_url = 'http://example.com/api'
        with self.settings(URL_API=new_url):
            self.assertEquals(BookmarkClient().base_url, new_url)

    def test_jwt_headers(self):
        headers = BookmarkClient()._get_headers()
        self.assertIn('JWT ', headers['Authorization'])

    def test_endpoint(self):
        endpoint = 'foobar'
        expected_endpoint = 'http://example.com/%s/' % endpoint
        with self.settings(URL_API='http://example.com'):
            client = BookmarkClient()
            self.assertEquals(client._get_url(endpoint), expected_endpoint)

    def test_endpoint_with_id(self):
        endpoint = 'foo'
        _id = randrange(1, 99)
        expected_endpoint = 'http://other-example.com/%s/%s' % (endpoint, _id)
        with self.settings(URL_API='http://other-example.com'):
            client = BookmarkClient()
            self.assertEquals(client._get_url(endpoint, _id), expected_endpoint)

    def test_login_success(self):
        httpretty.enable()
        httpretty.allow_net_connect = False
        # Mock responderá com token - sucesso no login
        httpretty.register_uri(httpretty.POST, self.url + '/auth/',
                               body='{"token": "any content"}',
                               content_type="application/json")
        self.assertTrue(self.bookmark_client.login(user='myuser', password='mypassword'))
        httpretty.disable()
        httpretty.reset()

    def test_login_error(self):
        httpretty.enable()
        httpretty.allow_net_connect = False
        # Mock responderá com erro - falha no login
        httpretty.register_uri(httpretty.POST, self.url + '/auth/', status=400)
        self.assertFalse(self.bookmark_client.login(user='other', password='anotherpassword'))
        httpretty.disable()
        httpretty.reset()

    def test_get_bookmarks(self):
        mock_content = []
        qtd_bookmarks = randrange(2, 10)
        for _ in range(qtd_bookmarks):
            mock_content.append(self.get_fake_bookmark())
        httpretty.enable()
        httpretty.allow_net_connect = False
        # Mock responderá com sucesso
        httpretty.register_uri(httpretty.GET, self.url + '/bookmarks/', json.dumps(mock_content))
        data = self.bookmark_client.get_bookmarks()
        self.assertEquals(len(data), qtd_bookmarks)
        httpretty.disable()
        httpretty.reset()

    def test_get_bookmarks_error(self):
        httpretty.enable()
        httpretty.allow_net_connect = False
        # Mock responderá com erro
        httpretty.register_uri(httpretty.GET, self.url + '/bookmarks/', status=400)
        self.assertEquals(self.bookmark_client.get_bookmarks(), [])
        httpretty.disable()
        httpretty.reset()

    def test_new_bookmark(self):
        bookmark_title = "New Test"
        bookmark_url = "http://example.com/test"
        httpretty.enable()
        httpretty.allow_net_connect = False
        # mock_api_content_create_bookmark irá retornar sucesso ou erro, dependendo dos parametros
        httpretty.register_uri(httpretty.POST, self.url + '/bookmarks/', body=self.mock_api_content_create_or_update_bookmark)
        self.assertTrue(self.bookmark_client.new_bookmark(bookmark_title, bookmark_url))
        httpretty.disable()
        httpretty.reset()

    def test_new_bookmark_error(self):
        bookmark_title = ""
        bookmark_url = ""
        httpretty.enable()
        httpretty.allow_net_connect = False
        # mock_api_content_create_bookmark irá retornar sucesso ou erro, dependendo dos parametros
        httpretty.register_uri(httpretty.POST, self.url + '/bookmarks/', body=self.mock_api_content_create_or_update_bookmark)
        self.assertFalse(self.bookmark_client.new_bookmark(bookmark_title, bookmark_url))
        httpretty.disable()
        httpretty.reset()

    def test_update_bookmark(self):
        _id = randrange(1, 1000)
        bookmark_title = "New Test"
        bookmark_url = "http://example.com/test"
        httpretty.enable()
        httpretty.allow_net_connect = False
        # mock_api_content_create_bookmark irá retornar sucesso ou erro, dependendo dos parametros
        httpretty.register_uri(httpretty.PUT, self.url + '/bookmarks/%d' % _id, body=self.mock_api_content_create_or_update_bookmark)
        self.assertTrue(self.bookmark_client.update_bookmark(_id, bookmark_title, bookmark_url))
        httpretty.disable()
        httpretty.reset()

    def test_update_bookmark_error(self):
        _id = randrange(1, 1000)
        bookmark_title = ""
        bookmark_url = ""
        httpretty.enable()
        httpretty.allow_net_connect = False
        # mock_api_content_create_bookmark irá retornar sucesso ou erro, dependendo dos parametros
        httpretty.register_uri(httpretty.PUT, self.url + '/bookmarks/%d' % _id, body=self.mock_api_content_create_or_update_bookmark)
        self.assertFalse(self.bookmark_client.update_bookmark(_id, bookmark_title, bookmark_url))
        httpretty.disable()
        httpretty.reset()

    def test_delete_bookmark(self):
        _id = 2 * randrange(1, 500)  # Força número par - É nossa flag para sucesso
        httpretty.enable()
        httpretty.allow_net_connect = False
        # mock_api_content_create_bookmark irá retornar sucesso ou erro, dependendo dos parametros
        httpretty.register_uri(httpretty.DELETE, self.url + '/bookmarks/%d' % _id, body=self.mock_api_content_delete_bookmark)
        self.assertTrue(self.bookmark_client.delete_bookmark(_id))
        httpretty.disable()
        httpretty.reset()

    def test_delete_bookmark_error(self):
        _id = 2 * randrange(1, 500) + 1  # Força número impar - É nossa flag para erro
        httpretty.enable()
        httpretty.allow_net_connect = False
        # mock_api_content_create_bookmark irá retornar sucesso ou erro, dependendo dos parametros
        httpretty.register_uri(httpretty.DELETE, self.url + '/bookmarks/%d' % _id, body=self.mock_api_content_delete_bookmark)
        self.assertFalse(self.bookmark_client.delete_bookmark(_id))
        httpretty.disable()
        httpretty.reset()

    def test_sign_in(self):
        httpretty.enable()
        httpretty.allow_net_connect = False
        # Mock responderá com sucesso
        httpretty.register_uri(httpretty.POST, self.url + '/users/',
                               body=self.mock_api_login_or_create_user)
        httpretty.register_uri(httpretty.POST, self.url + '/auth/',
                               body=self.mock_api_login_or_create_user)
        self.assertTrue(self.bookmark_client.sign_in(name='Foo', email='test@example.com', password='123456'))
        httpretty.disable()
        httpretty.reset()

    def test_sign_in_error(self):
        httpretty.enable()
        httpretty.allow_net_connect = False

        httpretty.register_uri(httpretty.POST, self.url + '/users/',
                               body=self.mock_api_login_or_create_user)
        httpretty.register_uri(httpretty.POST, self.url + '/auth/',
                               body=self.mock_api_login_or_create_user)
        # Mock responderá com erro
        self.assertFalse(self.bookmark_client.sign_in(name='Example', email='another-user@example.com', password='12345678'))
        httpretty.disable()
        httpretty.reset()


class LoginViewTest(MockAPIMixin, TestCase):
    def setUp(self):
        self.url = reverse('login')

    @override_settings(URL_API='http://example.com')
    def test_login_with_sucess(self):
        httpretty.enable()
        httpretty.allow_net_connect = True  # Precisa para a chamada a /login funcionar
        # mock_api_content_create_bookmark irá retornar sucesso ou erro, dependendo dos parametros
        httpretty.register_uri(httpretty.POST, 'http://example.com/auth/',
                               body=self.mock_api_login_or_create_user)
        # Dados habilitados para sucesso no mock
        post_data = {"username": "test@example.com", "password": "123456"}
        response = self.client.post(self.url, post_data)
        httpretty.disable()
        httpretty.reset()
        self.assertRedirects(response, reverse('dashboard'))

    @override_settings(URL_API='http://example.com')
    def test_login_session(self):
        httpretty.enable()
        httpretty.allow_net_connect = True  # Precisa para a chamada a /login funcionar
        # mock_api_content_create_bookmark irá retornar sucesso ou erro, dependendo dos parametros
        httpretty.register_uri(httpretty.POST, 'http://example.com/auth/',
                               body=self.mock_api_login_or_create_user)
        # Dados habilitados para sucesso no mock
        post_data = {"username": "test@example.com", "password": "123456"}
        response = self.client.post(self.url, post_data)
        httpretty.disable()
        httpretty.reset()
        self.assertEquals(self.client.session['user'], 'FAKE_TOKEN')

    @override_settings(URL_API='http://example.com')
    def test_login_with_error(self):
        httpretty.enable()
        httpretty.allow_net_connect = True  # Precisa para a chamada a /login funcionar
        # mock_api_content_create_bookmark irá retornar sucesso ou erro, dependendo dos parametros
        httpretty.register_uri(httpretty.POST, 'http://example.com/auth/',
                               body=self.mock_api_login_or_create_user)
        # Dados habilitados para sucesso no mock
        post_data = {"username": "another@example.com", "password": "12345678"}
        response = self.client.post(self.url, post_data)
        httpretty.disable()
        httpretty.reset()
        # Verifica se renderizou a página de login novamente
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.resolver_match.url_name, 'login')


class DashboardViewTest(MockAPIMixin, TestCase):
    def setUp(self):
        self.url = reverse('dashboard')
        self.do_login()

    @override_settings(URL_API='http://example.com')
    def do_login(self):
        httpretty.enable()
        httpretty.allow_net_connect = True  # Precisa para a chamada a /login funcionar
        # mock_api_content_create_bookmark irá retornar sucesso ou erro, dependendo dos parametros
        httpretty.register_uri(httpretty.POST, 'http://example.com/auth/',
                               body=self.mock_api_login_or_create_user)
        # Dados habilitados para sucesso no mock
        post_data = {"username": "test@example.com", "password": "123456"}
        self.client.post(reverse('login'), post_data)
        httpretty.disable()
        httpretty.reset()

    def do_logout(self):
        self.client.get(reverse('logout'))

    @override_settings(URL_API='http://example.com')
    def test_with_login(self):
        response = self.client.get(self.url)
        # Verifica se a página de dashboard foi renderizada
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.resolver_match.url_name, 'dashboard')

    def test_without_login(self):
        self.do_logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('login'))

    @override_settings(URL_API='http://example.com')
    def test_bookmarks(self):
        httpretty.enable()
        httpretty.allow_net_connect = True  # Precisa para a chamada a página funcionar
        httpretty.register_uri(httpretty.GET, 'http://example.com/bookmarks/',
                               body=self.mock_api_login_or_create_user)
        response = self.client.get(self.url)
        httpretty.disable()
        httpretty.reset()
        # Verifica se existe bookmarks no contexto enviado para o template
        self.assertIsNotNone(response.context['bookmarks'])

    @override_settings(URL_API='http://example.com')
    def test_create_new_bookmark(self):
        httpretty.enable()
        httpretty.allow_net_connect = True  # Precisa para a chamada a página funcionar
        httpretty.register_uri(httpretty.POST, 'http://example.com/bookmarks/',
                               body=self.mock_api_content_create_or_update_bookmark)
        httpretty.register_uri(httpretty.GET, 'http://example.com/bookmarks/',
                               body=self.mock_api_content_get_bookmarks)
        post_data = {"txtTitulo": "Criado pelo dashboard", "txtUrl": "http://outra.url.com.br/"}
        response = self.client.post(self.url, post_data)
        httpretty.disable()
        httpretty.reset()
        self.assertEquals(response.context_data['view'].user_message, 'Bookmark criado com sucesso')

    @override_settings(URL_API='http://example.com')
    def test_create_new_bookmark_error(self):
        httpretty.enable()
        httpretty.allow_net_connect = True  # Precisa para a chamada a página funcionar
        httpretty.register_uri(httpretty.POST, 'http://example.com/bookmarks/',
                               body=self.mock_api_content_create_or_update_bookmark)
        httpretty.register_uri(httpretty.GET, 'http://example.com/bookmarks/',
                               body=self.mock_api_content_get_bookmarks)
        post_data = {}
        response = self.client.post(self.url, post_data)
        httpretty.disable()
        httpretty.reset()
        self.assertEquals(response.context_data['view'].error_message, 'Não foi possível completar a operação')

    @override_settings(URL_API='http://example.com')
    def test_update_bookmark(self):
        _id = randrange(1, 1000)
        httpretty.enable()
        httpretty.allow_net_connect = True  # Precisa para a chamada a página funcionar
        httpretty.register_uri(httpretty.PUT, 'http://example.com/bookmarks/%d' % _id,
                               body=self.mock_api_content_create_or_update_bookmark)
        httpretty.register_uri(httpretty.GET, 'http://example.com/bookmarks/',
                               body=self.mock_api_content_get_bookmarks)

        post_data = {"__operation": "__update__", "__id": str(_id), "txtTitulo": "Alterado pelo dashboard", "txtUrl": "http://outra.url.com.br/"}
        response = self.client.post(self.url, post_data)
        httpretty.disable()
        httpretty.reset()
        self.assertEquals(response.context_data['view'].user_message, 'Bookmark atualizado com sucesso')

    @override_settings(URL_API='http://example.com')
    def test_update_bookmark_error(self):
        _id = randrange(1, 1000)
        httpretty.enable()
        httpretty.allow_net_connect = True  # Precisa para a chamada a página funcionar
        httpretty.register_uri(httpretty.PUT, 'http://example.com/bookmarks/%d' % _id,
                               body=self.mock_api_content_create_or_update_bookmark)
        httpretty.register_uri(httpretty.GET, 'http://example.com/bookmarks/',
                               body=self.mock_api_content_get_bookmarks)
        post_data = {"__operation": "__update__", "__id": str(_id)}
        response = self.client.post(self.url, post_data)
        httpretty.disable()
        httpretty.reset()
        self.assertEquals(response.context_data['view'].error_message, 'Não foi possível completar a operação')

    @override_settings(URL_API='http://example.com')
    def test_remove_bookmark(self):
        _id = 2 * randrange(1, 500)
        httpretty.enable()
        httpretty.allow_net_connect = True  # Precisa para a chamada a página funcionar
        httpretty.register_uri(httpretty.DELETE, 'http://example.com/bookmarks/%d' % _id,
                               body=self.mock_api_content_delete_bookmark)
        httpretty.register_uri(httpretty.GET, 'http://example.com/bookmarks/',
                               body=self.mock_api_content_get_bookmarks)

        post_data = {"__operation": "__remove__", "__id": str(_id), "txtTitulo": "Alterado pelo dashboard",
                     "txtUrl": "http://outra.url.com.br/"}
        response = self.client.post(self.url, post_data)
        httpretty.disable()
        httpretty.reset()
        self.assertEquals(response.context_data['view'].user_message, 'Bookmark removido com sucesso')

    @override_settings(URL_API='http://example.com')
    def test_remove_bookmark_error(self):
        _id = 2 * randrange(1, 500) + 1
        httpretty.enable()
        httpretty.allow_net_connect = True  # Precisa para a chamada a página funcionar
        httpretty.register_uri(httpretty.DELETE, 'http://example.com/bookmarks/%d' % _id,
                               body=self.mock_api_content_delete_bookmark)
        httpretty.register_uri(httpretty.GET, 'http://example.com/bookmarks/',
                               body=self.mock_api_content_get_bookmarks)
        post_data = {"__operation": "__remove__", "__id": str(_id)}
        response = self.client.post(self.url, post_data)
        httpretty.disable()
        httpretty.reset()
        self.assertEquals(response.context_data['view'].error_message, 'Não foi possível completar a operação')


class SignInViewTest(MockAPIMixin, TestCase):
    def setUp(self):
        self.url = reverse('sign-in')

    @override_settings(URL_API='http://example.com')
    def test_create_user_with_sucess(self):
        httpretty.enable()
        httpretty.allow_net_connect = True
        httpretty.register_uri(httpretty.POST, 'http://example.com/users/',
                               body=self.mock_api_login_or_create_user)
        httpretty.register_uri(httpretty.POST, 'http://example.com/auth/',
                               body=self.mock_api_login_or_create_user)
        # Dados habilitados para sucesso no mock
        post_data = {"name": "Fulano de Tal", "email": "test@example.com", "password": "123456", "confirm_password": "123456"}
        response = self.client.post(self.url, post_data)
        httpretty.disable()
        httpretty.reset()
        self.assertRedirects(response, reverse('dashboard'))

    @override_settings(URL_API='http://example.com')
    def test_create_user_with_error(self):
        httpretty.enable()
        httpretty.allow_net_connect = True  # Precisa para a chamada a /login funcionar
        # mock_api_content_create_bookmark irá retornar sucesso ou erro, dependendo dos parametros
        httpretty.register_uri(httpretty.POST, 'http://example.com/users/',
                               body=self.mock_api_login_or_create_user)
        httpretty.register_uri(httpretty.POST, 'http://example.com/auth/',
                               body=self.mock_api_login_or_create_user)
        # Dados habilitados para sucesso no mock
        post_data = {"name": "Fulano de Tal", "email": "another@example.com", "password": "12345678", "confirm_password": "12345678"}
        response = self.client.post(self.url, post_data)
        httpretty.disable()
        httpretty.reset()
        # Verifica se renderizou a página de login novamente
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.resolver_match.url_name, 'sign-in')
        self.assertEquals(response.context_data['view'].error_message, 'Não foi possível completar a operação')

    def test_create_user_password_does_not_match(self):
        httpretty.enable()
        httpretty.allow_net_connect = True  # Precisa para a chamada a /login funcionar
        # mock_api_content_create_bookmark irá retornar sucesso ou erro, dependendo dos parametros
        httpretty.register_uri(httpretty.POST, 'http://example.com/users/',
                               body=self.mock_api_login_or_create_user)
        httpretty.register_uri(httpretty.POST, 'http://example.com/auth/',
                               body=self.mock_api_login_or_create_user)
        # Dados habilitados para sucesso no mock
        post_data = {"name": "Fulano de Tal", "email": "another@example.com", "password": "123456", "confirm_password": "12345678"}
        response = self.client.post(self.url, post_data)
        httpretty.disable()
        httpretty.reset()
        # Verifica se renderizou a página de login novamente
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.resolver_match.url_name, 'sign-in')
        self.assertEquals(response.context_data['view'].error_message, 'Senhas não conferem')

    def test_create_user_empty(self):
        httpretty.enable()
        httpretty.allow_net_connect = True  # Precisa para a chamada a /login funcionar
        # mock_api_content_create_bookmark irá retornar sucesso ou erro, dependendo dos parametros
        httpretty.register_uri(httpretty.POST, 'http://example.com/users/',
                               body=self.mock_api_login_or_create_user)
        httpretty.register_uri(httpretty.POST, 'http://example.com/auth/',
                               body=self.mock_api_login_or_create_user)
        # Dados habilitados para sucesso no mock
        post_data = {}
        response = self.client.post(self.url, post_data)
        httpretty.disable()
        httpretty.reset()
        # Verifica se renderizou a página de login novamente
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.resolver_match.url_name, 'sign-in')
        self.assertEquals(response.context_data['view'].error_message, 'Por favor preencha todos os campos')