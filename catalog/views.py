from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
import re
import requests
from django.conf import settings
import logging
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import User, Image, Like
from .forms import CustomUserCreationForm, LoginForm
from django.views.decorators.http import require_POST
import json
from django.contrib import messages
from django.db import models
from django.db.models import Count
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user = authenticate(
                request, 
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1']
            )
            if user is not None:
                message = f"🎉 Новый пользователь!\nЛогин: {form.cleaned_data['username']}\nEmail: {form.cleaned_data['email']}"
                send_telegram_notification(message)
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
    if request.user != user:  
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
            like.delete()

        likes_count = Like.objects.filter(image=image).count()

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
