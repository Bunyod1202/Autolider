from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from telebot import TeleBot
from telebot.types import Update

from bot.factory import bot_initializer
from bot.utils.constants import TOKEN
import re

from quizzes.models import Theme, Option, Quiz
import random
from tests.models import Test, Exam, ExamAccess, ExamAttempt, AttemptQuestion
from users.models import User
from subscriptions.utils import refresh_user_active_status
from bot.utils.helpers import normalize_phone_number
from django.utils import timezone

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
    user_id = request.GET.get('user_id')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({
            'ok': False,
            'error': f'User with id={user_id} not found.'
        }, status=404)

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
def theme_list_view(request):
    user: User = User.objects.get(id=request.GET.get('user_id'))
    # Sync active status before showing themes
    refresh_user_active_status(user)
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
                } for test in user.tests.filter(theme=theme).order_by('-added_time','-id')
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
        # Build randomized quiz order for this session
        active_quizzes = list(theme.quizzes.filter(is_active=True))
        random.shuffle(active_quizzes)

        return render(
            request,
            'test.html',
            context={
                'user': user,
                'theme': {
                    'id': theme.id,
                    'name': theme.name(user.text.language),
                    'quizzes_count': len(active_quizzes),
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
                        } for quiz in active_quizzes
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




@csrf_exempt
def exams_view(request):
    user_id = request.GET.get('user_id')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'ok': False, 'error': f'user {user_id} not found'}, status=404)

    # if phone missing, render phone form inside WebApp
    phone_missing = not bool(user.phone_number)
    now = timezone.now()
    accesses = ExamAccess.objects.filter(user=user, exam__is_active=True).select_related('exam').order_by('exam__date')
    exams = []
    for acc in accesses:
        ex = acc.exam
        exams.append({
            'id': ex.id,
            'title': ex.title,
            'date': ex.date.strftime('%Y-%m-%d %H:%M'),
            'started': ex.date <= now,
            'type': ex.type,
            'question_count': ex.question_count,
        })
    return render(request, 'exams.html', {
        'user': user,
        'phone_missing': phone_missing,
        'exams': exams,
    })


@csrf_exempt
def exams_save_phone_view(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
    user_id = request.POST.get('user_id')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'ok': False, 'error': f'user {user_id} not found'}, status=404)
    norm = normalize_phone_number(request.POST.get('phone', ''))
    if not norm:
        return render(request, 'exams.html', {
            'user': user,
            'phone_missing': True,
            'error': 'Telefon raqam formati noto\'g\'ri',
            'exams': [],
        })
    user.phone_number = norm
    user.save(update_fields=['phone_number'])
    return redirect(f"/bot/exams/?user_id={user.id}")


@csrf_exempt
def exam_start_view(request, exam_id: int):
    user_id = request.GET.get('user_id') or request.POST.get('user_id')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'ok': False, 'error': f'user {user_id} not found'}, status=404)
    # Access and timing checks
    try:
        exam = Exam.objects.get(id=exam_id, is_active=True)
    except Exam.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Exam not found'}, status=404)
    if not ExamAccess.objects.filter(user=user, exam=exam).exists():
        return render(request, 'exam.html', {'user': user, 'error': 'Sizga imtihon ruxsati berilmagan'})
    if exam.date > timezone.now():
        return render(request, 'exam.html', {'user': user, 'error': 'Imtihon vaqti hali boshlanmagan'})

    # Resume or create attempt with random questions
    attempt = ExamAttempt.objects.filter(exam=exam, user=user, finished_at__isnull=True).first()
    if not attempt:
        # Ensure default topics for MID types if none selected
        if exam.type != Exam.Type.FINAL and exam.topics.count() == 0:
            try:
                from quizzes.models import Theme
                if exam.type == Exam.Type.MID_1:
                    a, b = 1, 11
                elif exam.type == Exam.Type.MID_2:
                    a, b = 12, 22
                else:
                    a, b = 23, 29
                selected_topics = list(Theme.objects.filter(is_active=True, order__gte=a, order__lte=b))
                if not selected_topics:
                    active = list(Theme.objects.filter(is_active=True).order_by('order', 'id'))
                    selected_topics = [t for i, t in enumerate(active, start=1) if a <= i <= b]
                if selected_topics:
                    exam.topics.add(*selected_topics)
            except Exception:
                pass
        # build pool
        if exam.type == Exam.Type.FINAL:
            pool = list(Quiz.objects.filter(is_active=True))
        else:
            pool = list(Quiz.objects.filter(is_active=True, theme__in=exam.topics.all()))
        if len(pool) < exam.question_count:
            return render(request, 'exam.html', {'user': user, 'error': 'Savollar yetarli emas'})
        selected = random.sample(pool, exam.question_count)
        attempt = ExamAttempt.objects.create(exam=exam, user=user, total_questions=exam.question_count)
        AttemptQuestion.objects.bulk_create([
            AttemptQuestion(attempt=attempt, question=q, order=i+1) for i, q in enumerate(selected)
        ])

    # Build questions data for WebApp
    qitems = []
    for aq in attempt.attempt_questions.select_related('question').order_by('order'):
        quiz = aq.question
        qitems.append({
            'id': quiz.id,
            'order': aq.order,
            'question': quiz.question(user.text.language),
            'image_url': quiz.image_url,
            'options': [
                {'id': opt.id, 'text': opt.text(user.text.language)} for opt in quiz.options.all()
            ],
            'answer_id': aq.user_answer_id or 0,
        })
    return render(request, 'exam.html', {
        'user': user,
        'attempt': attempt,
        'exam': exam,
        'questions': qitems,
    })


@csrf_exempt
def exam_answer_view(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
    user_id = request.POST.get('user_id')
    attempt_id = request.POST.get('attempt_id')
    qid = int(request.POST.get('question_id'))
    oid = int(request.POST.get('option_id'))
    try:
        user = User.objects.get(id=user_id)
        attempt = ExamAttempt.objects.get(id=attempt_id, user=user)
        aq = attempt.attempt_questions.select_related('question').get(question_id=qid)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Not found'}, status=404)
    from quizzes.models import Option as Opt
    try:
        opt = Opt.objects.get(id=oid, quiz_id=qid)
    except Opt.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Option not found'}, status=404)
    aq.user_answer_id = opt.id
    aq.is_correct = bool(opt.is_correct)
    aq.save(update_fields=['user_answer', 'is_correct'])
    return JsonResponse({'ok': True})


@csrf_exempt
def exam_finish_view(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
    user_id = request.POST.get('user_id')
    attempt_id = request.POST.get('attempt_id')
    spent_seconds = int(request.POST.get('spent_seconds', 0))
    try:
        user = User.objects.get(id=user_id)
        attempt = ExamAttempt.objects.get(id=attempt_id, user=user)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Not found'}, status=404)
    attempt.correct_count = attempt.attempt_questions.filter(is_correct=True).count()
    attempt.wrong_count = attempt.total_questions - attempt.correct_count
    attempt.spent_time = spent_seconds
    attempt.finished_at = timezone.now()
    attempt.save(update_fields=['correct_count', 'wrong_count', 'spent_time', 'finished_at'])
    return JsonResponse({'ok': True, 'result_url': f"/bot/exams/result/{attempt.id}/"})


@csrf_exempt
def exam_result_view(request, attempt_id: int):
    try:
        attempt = ExamAttempt.objects.select_related('user', 'exam').get(id=attempt_id)
    except ExamAttempt.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Not found'}, status=404)
    user = attempt.user
    answers = []
    for aq in attempt.attempt_questions.select_related('question', 'user_answer').order_by('order'):
        quiz = aq.question
        answers.append({
            'order': aq.order,
            'question': quiz.question(user.text.language),
            'image_url': quiz.image_url,
            'options': [
                {'id': opt.id, 'text': opt.text(user.text.language), 'is_correct': opt.is_correct}
                for opt in quiz.options.all()
            ],
            'user_answer_id': aq.user_answer_id,
            'is_correct': aq.is_correct,
        })
    return render(request, 'exam-result.html', {
        'user': user,
        'exam': attempt.exam,
        'attempt': attempt,
        'answers': answers,
    })
