from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # A Landing Page ('') e a Gestão ('dashboard/') ficam centralizadas aqui:
    path('', include('apps.management.urls')),
    
    # Demais módulos
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('courses/', include('apps.courses.urls')),
    path('quizzes/', include('apps.quizzes.urls')),
    path('certificates/', include('apps.certificates.urls')),
    path('auth/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)