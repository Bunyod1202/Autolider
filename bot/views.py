from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from telebot import TeleBot
from telebot.types import Update

from bot.factory import bot_initializer
from bot.utils.constants import TOKEN
from quizzes.models import Theme, Option
from tests.models import Test
from users.models import User
from subscriptions.utils import refresh_user_active_status

bot: TeleBot = bot_initializer(TOKEN)



@csrf_exempt
def web_hook_view(request, token):
    if token == TOKEN:
        if request.headers.get('content-type') == 'application/json':
            try:
                json_string = request.body.decode('utf-8')
                update = Update.de_json(json_string)
                bot.process_new_updates([update])
                return JsonResponse({'ok': True})
            except Exception as e:
                print(f"Webhook xatosi: {e}")
                return JsonResponse({'ok': False, 'description': str(e)})
        else:
            return JsonResponse({'ok': False, 'description': 'Incorrect format of content type.'})
    else:
        return JsonResponse({'ok': False, 'description': "😐😐😐"})


@csrf_exempt
def help_view(request):
    user: User = User.objects.get(id=request.GET.get('user_id'))
    return render(
        request,
        'help.html',
        context={
            'title': user.text.help,
            'help_info': user.text.help_info,
        }
    )


@csrf_exempt
def theme_list_view(request):
    user: User = User.objects.get(id=request.GET.get('user_id'))
    return render(
        request,
        'themes.html',
        context={
            'user': user,
            'themes': [
                {
                    'id': theme.id,
                    'name': theme.name(user.text.language),
                    'quizzes_count': theme.quizzes.filter(is_active=True).count(),
                } for theme in Theme.objects.filter(is_active=True)
            ],
        }
    )


@csrf_exempt
def theme_detail_view(request, theme_id: int):
    user: User = User.objects.get(id=request.POST.get('user_id'))
    theme: Theme = Theme.objects.get(id=theme_id)
    return render(
        request,
        'theme.html',
        context={
            'user': user,
            'theme': {
                'id': theme.id,
                'name': theme.name(user.text.language),
                'quizzes_count': theme.quizzes.filter(is_active=True).count(),
            },
            'tests': [
                {
                    'id': test.id,
                    'spent_time': test.spent_time,
                    'correct_answers': test.correct_answers,
                    'added_time': test.added_time.strftime('%Y-%m-%d %H:%M:%S'),
                } for test in user.tests.filter(theme=theme)
            ],
        }
    )


@csrf_exempt
def test_view(request):
    user: User = User.objects.get(id=request.POST.get('user_id'))
    # Sync user's active status with subscriptions before allowing access
    refresh_user_active_status(user)
    if user.is_active:
        theme: Theme = Theme.objects.get(id=request.POST.get('theme_id'))
        return render(
            request,
            'test.html',
            context={
                'user': user,
                'theme': {
                    'id': theme.id,
                    'name': theme.name(user.text.language),
                    'quizzes_count': theme.quizzes.filter(is_active=True).count(),
                    'quizzes': [
                        {
                            'id': quiz.id,
                            'question': quiz.question(user.text.language),
                            'image_url': quiz.image_url,
                            'options': [
                                {
                                    'id': option.id,
                                    'text': option.text(user.text.language),
                                    'is_correct': option.is_correct,
                                } for option in quiz.options.all()
                            ],
                            'answer': quiz.options.filter(is_correct=True).first(),
                        } for quiz in theme.quizzes.filter(is_active=True)
                    ]
                },
            }
        )
    return redirect('/bot/themes/')


@csrf_exempt
def save_test_view(request):
    user: User = User.objects.get(id=request.POST.get('user_id'))
    # Sync user's active status with subscriptions before saving results
    refresh_user_active_status(user)
    if user.is_active:
        theme: Theme = Theme.objects.get(id=request.POST.get('theme_id'))
        spent_seconds = int(request.POST.get('spent_seconds', 0))
        selected_options = Option.objects.filter(id__in=list(map(int, request.POST.get('selected_options', '').split(','))))
        test: Test = Test.objects.create(
            user=user,
            theme=theme,
            quizzes_count=theme.quizzes.count(),
            correct_answers_count=selected_options.filter(is_correct=True).count(),
            spent_seconds=spent_seconds,
        )
        test.selected_options.add(*selected_options)
        return test_result_view(request, test.id)
    return redirect('/bot/themes/')


@csrf_exempt
def test_result_view(request, test_id: int):
    test: Test = Test.objects.get(id=test_id)
    return render(
        request,
        'test-result.html',
        context={
            'user': test.user,
            'test': {
                'id': test.id,
                'theme': test.theme.name(test.user.text.language),
                'theme_id': test.theme.id,
                'user_id': test.user.id,
                'spent_time': test.spent_time,
                'correct_answers': test.correct_answers,
                'added_time': test.added_time.strftime('%Y-%m-%d %H:%M:%S'),
                'answers': [
                    {
                        'quiz': {
                            'question': answer.quiz.question(test.user.text.language),
                            'image_url': answer.quiz.image_url,
                            'options': [
                                {
                                    'id': option.id,
                                    'text': option.text(test.user.text.language),
                                    'is_correct': option.is_correct,
                                } for option in answer.quiz.options.all()
                            ]
                        },
                        'answer': {
                            'id': answer.id,
                            'text': answer.text(test.user.text.language),
                        }
                    } for answer in test.selected_options.all()
                ]
            }
        }
    )
