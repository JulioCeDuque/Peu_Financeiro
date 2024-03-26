from django.urls import path
from app_pronct import views
from django.contrib.auth import views as auth_views
from .views import exportar_dados


urlpatterns = [

    path('cadastro/', views.cadastro, name='cadastro'),
    path('', views.login, name='login'),
    path('home/', views.plataforma, name='plataforma'),
    path('dados_do_grafico/', views.dados_do_grafico, name='dados_do_grafico'),
    path('logout/', views.auth_logout, name='auth_logout'),
    path('cadastro_externo/', views.cadastro_externo, name='cadastro_externo'),
    path('internos/', views.lista_usuarios, name='lista_usuarios'),
    path('cadastro_financeiro/', views.cadastro_financeiro, name='cadastro_financeiro'),
    # path('lista_clientes/', views.lista_clientes, name='lista_clientes'),
    path('verificar_cpf/', views.verificar_cpf, name='verificar_cpf'),
    # path('lista_clientes/<str:cpf>/servicos/', views.servicos_cliente, name='servicos_cliente'),
    path('relatorios', views.teste_cliente, name='teste_cliente'),
    path('relatorios/<int:id>/gerais/', views.informacoes_gerais, name='informacoes_gerais'),
    
    path('password_reset/', auth_views.PasswordResetView.as_view(), name="password_reset"),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('exportar-dados/', exportar_dados, name='exportar_dados')]