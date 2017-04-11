# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import RedirectView
from django.views.generic import TemplateView

from bookmarks_client.bookmarks.client import BookmarkClient


class HomeView(TemplateView):
    template_name = 'home.html'


class LoginView(TemplateView):
    template_name = 'login.html'

    def post(self, request, *args, **kwargs):
        client = BookmarkClient()
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        if username and password:
            if client.login(username, password):
                request.session['user'] = client.token
                return redirect('dashboard')
        return self.get(request, *args, **kwargs)


class LogoutView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        # Limpa o token do usuário da sessão. É isso que de fato efetua o logout
        self.request.session['user'] = ''
        return reverse('home')


class DashboardView(TemplateView):
    template_name = 'dashboard.html'
    token = ''

    def dispatch(self, request, *args, **kwargs):
        self.token = request.session.get('user', '')
        if not self.token:
            return redirect('login')
        return super(DashboardView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        client = BookmarkClient(self.token)
        bookmarks = client.get_bookmarks()
        context['bookmarks'] = bookmarks
        return context

    def post(self, request, *args, **kwargs):
        self.user_message = ''
        self.error_message = ''
        client = BookmarkClient(self.token)
        __operation = request.POST.get('__operation')
        _id = request.POST.get('__id')
        titulo = request.POST.get('txtTitulo')
        url = request.POST.get('txtUrl')
        if __operation == '__remove__':
            if client.delete_bookmark(_id):
                self.user_message = 'Bookmark removido com sucesso'
            else:
                self.error_message = 'Não foi possível completar a operação'
        elif __operation == '__update__':
            if client.update_bookmark(_id, titulo, url):
                self.user_message = 'Bookmark atualizado com sucesso'
            else:
                self.error_message = 'Não foi possível completar a operação'
        else:
            if client.new_bookmark(titulo, url):
                self.user_message = 'Bookmark criado com sucesso'
            else:
                self.error_message = 'Não foi possível completar a operação'
        return self.get(request, *args, **kwargs)
