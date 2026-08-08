from django.urls import path
from . import views

app_name = 'management'

urlpatterns = [
    # 🌟 Nova Rota da Landing Page SaaS na raiz (/)
    path('', views.landing_page_view, name='landing_page'),

    # Painel de Gestão, BI e Métricas para Administradores
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('matriculas/', views.enrollment_list_view, name='enrollment_list'),
    path('matriculas/<int:enrollment_id>/<str:action>/', views.enrollment_action_view, name='enrollment_action'),
    path('financeiro/', views.financial_list_view, name='financial_list'),
    path('financeiro/baixa/<int:payment_id>/', views.register_payment_view, name='register_payment'),

    # 💳 Rotas de Checkout e Webhook (Mercado Pago)
    path('pagar/', views.criar_pagamento_mercadopago, name='criar_pagamento'),
    path('pagamentos/webhook/', views.mercadopago_webhook, name='mercadopago_webhook'),
]