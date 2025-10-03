from django.urls import path
from bot.views import web_hook_view, help_view, theme_list_view, theme_detail_view, test_view, save_test_view, test_result_view

urlpatterns = [
    path('help/', help_view),
    path('themes/', theme_list_view),
    path('themes/<int:theme_id>/', theme_detail_view),
    path('test/', test_view),
    path('save-test/', save_test_view),
    path('test/<int:test_id>/', test_result_view),
    path('<str:token>/', web_hook_view),
]
