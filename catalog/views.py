from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
import re
import requests
from django.conf import settings
import logging
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import User, Image, Like
from .forms import CustomUserCreationForm, LoginForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
import json
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm, LoginForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import Image, Like
import json
from django.db import models
from django.db.models import Count
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import Image, Like
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Аутентифицируем пользователя с email, а не username, так как USERNAME_FIELD = 'email'
            user = authenticate(
                request, 
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1']
            )
            if user is not None:
                login(request, user)
                return redirect('profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'catalog/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('profile')
        else:
            return render(request, 'catalog/login.html', {
                'form': form,
                'error': 'Неверный логин или пароль'
            })
    else:
        form = LoginForm()
    return render(request, 'catalog/login.html', {'form': form})

def is_admin(user):
    return user.is_authenticated and user.is_admin

def register_old(request):
    errors = {}
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        email = request.POST.get('email', '')

        if User.objects.filter(username=username).exists():
            errors['username'] = 'Этот логин уже занят'

        if not re.match(r'^[A-Za-z0-9_]{3,20}$', username):
            errors['username'] = 'Только латиница, цифры и _ (3-20 символов)'

        if not re.match(r'^(?=.*[A-Z])(?=.*\d).{8,}$', password):
            errors['password'] = 'Нужно 8+ символов, 1 заглавная буква и 1 цифра'

        if not errors:
            try:
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email
                )
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    message = f"🎉 Новый пользователь!\nЛогин: {username}\nEmail: {email}"
                    send_telegram_notification(message)
                    return redirect('index')
            except Exception as e:
                logger.error(f"Ошибка создания пользователя: {e}")
                errors['general'] = 'Ошибка регистрации. Попробуйте позже.'

    return render(request, 'catalog/register.html', {'errors': errors})


User = get_user_model()

def send_telegram_notification(text):
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    try:
        response = requests.post(url, json={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        })
        logger.info(f"Response from Telegram API: {response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"Ошибка отправки в Telegram: {e}")


def send_telegram_notification_old(text):
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    try:
        response = requests.post(url, json={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        })
        logger.info(f"Response from Telegram API: {response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"Ошибка отправки в Telegram: {e}")

def check_username(request):
    username = request.GET.get('username', '')
    exists = User.objects.filter(username=username).exists()
    return JsonResponse({'exists': exists})

def index(request):
    return render(request, 'catalog/index.html')

def racing(request):
    return render(request, 'catalog/racing.html')

@login_required
def profile(request):
    return render(request, 'catalog/profile.html', {
        'user': request.user
    })

def user_logout(request):
    logout(request)
    request.session.flush()
    return redirect('index')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_management(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'catalog/user_management.html', {'users': users})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.user != user:  # Нельзя удалить себя
        user.delete()
        messages.success(request, f'Пользователь {user.username} удален')
    return redirect('user_management')

@csrf_exempt
@login_required
def toggle_like(request, image_id):
    if request.method == 'POST':
        try:
            image = Image.objects.get(id=image_id)
        except Image.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Картинка не найдена'})

        like, created = Like.objects.get_or_create(user=request.user, image=image)
        if not created:
            # Уже был лайк — убираем
            like.delete()

        # Получаем новое количество лайков
        likes_count = Like.objects.filter(image=image).count()

        # Отправляем сообщение по WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "likes_group",
            {
                "type": "like_message",
                "image_id": image_id,
                "likes_count": likes_count
            }
        )

        return JsonResponse({'success': True, 'likes_count': likes_count})

    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})

def get_likes(request):
    images = Image.objects.annotate(likes_count=Count('like')).values('id', 'likes_count')
    return JsonResponse(list(images), safe=False)

def media(request):
    images = Image.objects.all().distinct() 
    images = Image.objects.all().prefetch_related('like_set')
    user_likes = []
    if request.user.is_authenticated:
        user_likes = Like.objects.filter(user=request.user).values_list('image_id', flat=True)
    
    return render(request, 'catalog/media.html', {
        'images': images,
        'user_likes': list(user_likes)
    })