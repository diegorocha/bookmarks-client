from bookmarks_client.bookmarks import views
from django.conf.urls import url

urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'^sign-in$', views.SignInView.as_view(), name='sign-in'),
    url(r'^login$', views.LoginView.as_view(), name='login'),
    url(r'^logout$', views.LogoutView.as_view(), name='logout'),
    url(r'^dashboard$', views.DashboardView.as_view(), name='dashboard'),
    url(r'^dashboard/users$', views.AllUsersView.as_view(), name='all-users'),
]
