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
        username = request.POST['username']
        password = request.POST['password']
        if client.login(username, password):
            request.session['user'] = client.token
            return redirect('dashboard')
        return self.get(request, *args, **kwargs)


class LogoutView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
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
        client = BookmarkClient(self.token)
        __operation = request.POST.get('__operation')
        _id = request.POST.get('__id')
        titulo = request.POST['txtTitulo']
        url = request.POST['txtUrl']
        if __operation == '__remove__':
            client.delete_bookmark(_id)
        elif __operation == '__update__':
            client.update_bookmark(_id, titulo, url)
        else:
            client.new_bookmark(titulo, url)
        return self.get(request, *args, **kwargs)
