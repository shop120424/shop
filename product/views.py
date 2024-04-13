from django.shortcuts import render, redirect

# Класс HttpResponse из пакета django.http, который позволяет отправить текстовое содержимое.
from django.http import HttpResponse, HttpResponseNotFound
# Конструктор принимает один обязательный аргумент – путь для перенаправления. Это может быть полный URL (например, 'https://www.yahoo.com/search/') или абсолютный путь без домена (например, '/search/').
from django.http import HttpResponseRedirect

from django.urls import reverse

from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages

from django.db.models import Max
from django.db.models import Q

from datetime import datetime, timedelta

# Отправка почты
from django.core.mail import send_mail

# Подключение моделей
from .models import Category, Catalog, ViewCatalog, Review, Question, News
# Подключение форм
from .forms import CategoryForm, CatalogForm, ReviewForm, QuestionCreateForm, QuestionEditForm, NewsForm, SignUpForm

from django.db.models import Sum

from django.db import models

import sys

import math

#from django.utils.translation import ugettext as _
from django.utils.translation import gettext_lazy as _

from django.utils.decorators import method_decorator
from django.views.generic import UpdateView
from django.contrib.auth.models import User
from django.urls import reverse_lazy

from django.contrib.auth import login as auth_login

from django.db.models.query import QuerySet

import csv
import xlwt
from io import BytesIO

# Create your views here.
# Групповые ограничения
def group_required(*group_names):
    """Requires user membership in at least one of the groups passed in."""
    def in_groups(u):
        if u.is_authenticated:
            if bool(u.groups.filter(name__in=group_names)) | u.is_superuser:
                return True
        return False
    return user_passes_test(in_groups, login_url='403')

###################################################################################################

# Стартовая страница 
def index(request):
    try:
        catalog = ViewCatalog.objects.all().order_by('?')[0:4]
        review = Review.objects.all().order_by('?')[0:4]
        news1 = News.objects.all().order_by('-daten')[0:1]
        news24 = News.objects.all().order_by('-daten')[1:4]
        return render(request, "index.html", {"catalog": catalog, "review": review, "news1": news1, "news24": news24})    
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)    

# Контакты
def contact(request):
    try:
        return render(request, "contact.html")
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

###################################################################################################
# Отчеты
@login_required
@group_required("Managers")
def report_index(request):
    try:        
        return render(request, "report/index.html")        
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)


###################################################################################################

# Список для изменения с кнопками создать, изменить, удалить
@login_required
@group_required("Managers")
def category_index(request):
    try:
        category = Category.objects.all().order_by('category_title')
        return render(request, "category/index.html", {"category": category,})
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# В функции create() получаем данные из запроса типа POST, сохраняем данные с помощью метода save()
# и выполняем переадресацию на корень веб-сайта (то есть на функцию index).
@login_required
@group_required("Managers")
def category_create(request):
    try:
        if request.method == "POST":
            category = Category()
            category.category_title = request.POST.get("category_title")
            categoryform = CategoryForm(request.POST)
            if categoryform.is_valid():
                category.save()
                return HttpResponseRedirect(reverse('category_index'))
            else:
                return render(request, "category/create.html", {"form": categoryform})
        else:        
            categoryform = CategoryForm()
            return render(request, "category/create.html", {"form": categoryform})
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Функция edit выполняет редактирование объекта.
@login_required
@group_required("Managers")
def category_edit(request, id):
    try:
        category = Category.objects.get(id=id)
        if request.method == "POST":
            category.category_title = request.POST.get("category_title")
            categoryform = CategoryForm(request.POST)
            if categoryform.is_valid():
                category.save()
                return HttpResponseRedirect(reverse('category_index'))
            else:
                return render(request, "category/edit.html", {"form": categoryform})
        else:
            # Загрузка начальных данных
            categoryform = CategoryForm(initial={'category_title': category.category_title, })
            return render(request, "category/edit.html", {"form": categoryform})
    except Category.DoesNotExist:
        return HttpResponseNotFound("<h2>Category not found</h2>")
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Удаление данных из бд
# Функция delete аналогичным функции edit образом находит объет и выполняет его удаление.
@login_required
@group_required("Managers")
def category_delete(request, id):
    try:
        category = Category.objects.get(id=id)
        category.delete()
        return HttpResponseRedirect(reverse('category_index'))
    except Category.DoesNotExist:
        return HttpResponseNotFound("<h2>Category not found</h2>")
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Просмотр страницы read.html для просмотра объекта.
@login_required
@group_required("Managers")
def category_read(request, id):
    try:
        category = Category.objects.get(id=id) 
        return render(request, "category/read.html", {"category": category})
    except Category.DoesNotExist:
        return HttpResponseNotFound("<h2>Category not found</h2>")
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

####################################################################

# Список для изменения с кнопками создать, изменить, удалить
@login_required
@group_required("Managers")
def catalog_index(request):
    catalog = Catalog.objects.all().order_by('catalog_title')
    return render(request, "catalog/index.html", {"catalog": catalog})
    
# Список для просмотра и отправки в корзину
#@login_required
#@group_required("Managers")
#@login_required
def catalog_list(request):
    try:
        # Каталог доступных товаров
        catalog = ViewCatalog.objects.all().order_by('category').order_by('catalog_title')
        # Категории и подкатегория товара (для поиска)
        category = Category.objects.all().order_by('category_title')
        if request.method == "POST":
            # Определить какая кнопка нажата
            if 'searchBtn' in request.POST:
                # Поиск по категории товара
                selected_item_category = request.POST.get('item_category')
                #print(selected_item_category)
                if selected_item_category != '-----':
                    category_query = Category.objects.filter(category_title = selected_item_category).only('id').all()
                    catalog = catalog.filter(category_id__in = category_query).all()
                # Поиск по названию товара
                catalog_search = request.POST.get("catalog_search")
                #print(catalog_search)                
                if catalog_search != '':
                    catalog = catalog.filter(catalog_title__contains = catalog_search).all()
                # Сортировка
                sort = request.POST.get('radio_sort')
                #print(sort)
                direction = request.POST.get('checkbox_sort_desc')
                #print(direction)
                if sort=='title':                    
                    if direction=='ok':
                        catalog = catalog.order_by('-catalog_title')
                    else:
                        catalog = catalog.order_by('catalog_title')
                elif sort=='price':                    
                    if direction=='ok':
                        catalog = catalog.order_by('-price')
                    else:
                        catalog = catalog.order_by('price')
                elif sort=='category':                    
                    if direction=='ok':
                        catalog = catalog.order_by('-category')
                    else:
                        catalog = catalog.order_by('category')
                return render(request, "catalog/list.html", {"catalog": catalog, "category": category, "selected_item_category": selected_item_category, "catalog_search": catalog_search, "sort": sort, "direction": direction,})    
            else:          
                return render(request, "catalog/list.html", {"catalog": catalog, "category": category,})    
        else:
            return render(request, "catalog/list.html", {"catalog": catalog, "category": category, })            
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# В функции create() получаем данные из запроса типа POST, сохраняем данные с помощью метода save()
# и выполняем переадресацию на корень веб-сайта (то есть на функцию index).
@login_required
@group_required("Managers")
def catalog_create(request):
    try:
        if request.method == "POST":
            catalog = Catalog()
            catalog.category = Category.objects.filter(id=request.POST.get("category")).first()
            catalog.catalog_title = request.POST.get("catalog_title")
            catalog.details = request.POST.get("details")        
            catalog.price = request.POST.get("price")
            if "photo" in request.FILES:                
                catalog.photo = request.FILES["photo"]
            catalogform = CatalogForm(request.POST)
            if catalogform.is_valid():
                catalog.save()
                return HttpResponseRedirect(reverse('catalog_index'))
            else:
                return render(request, "catalog/create.html", {"form": catalogform})
        else:        
            catalogform = CatalogForm()
            return render(request, "catalog/create.html", {"form": catalogform, })
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Функция edit выполняет редактирование объекта.
# Функция в качестве параметра принимает идентификатор объекта в базе данных.
@login_required
@group_required("Managers")
def catalog_edit(request, id):
    try:
        catalog = Catalog.objects.get(id=id) 
        if request.method == "POST":
            catalog.category = Category.objects.filter(id=request.POST.get("category")).first()
            catalog.catalog_title = request.POST.get("catalog_title")
            catalog.details = request.POST.get("details")        
            catalog.price = request.POST.get("price")
            if "photo" in request.FILES:                
                catalog.photo = request.FILES["photo"]
            catalogform = CatalogForm(request.POST)
            if catalogform.is_valid():
                catalog.save()
                return HttpResponseRedirect(reverse('catalog_index'))
            else:
                return render(request, "catalog/edit.html", {"form": catalogform})            
        else:
            # Загрузка начальных данных
            catalogform = CatalogForm(initial={'category': catalog.category, 'catalog_title': catalog.catalog_title, 'details': catalog.details, 'price': catalog.price, 'photo': catalog.photo })
            #print('->',catalog.photo )
            return render(request, "catalog/edit.html", {"form": catalogform})
    except Catalog.DoesNotExist:
        return HttpResponseNotFound("<h2>Catalog not found</h2>")
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Удаление данных из бд
# Функция delete аналогичным функции edit образом находит объет и выполняет его удаление.
@login_required
@group_required("Managers")
def catalog_delete(request, id):
    try:
        catalog = Catalog.objects.get(id=id)
        catalog.delete()
        return HttpResponseRedirect(reverse('catalog_index'))
    except Catalog.DoesNotExist:
        return HttpResponseNotFound("<h2>Catalog not found</h2>")
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Просмотр страницы с информацией о товаре для менеджера.
@login_required
@group_required("Managers")
def catalog_read(request, id):
    try:
        catalog = ViewCatalog.objects.get(id=id) 
        return render(request, "catalog/read.html", {"catalog": catalog})
    except Catalog.DoesNotExist:
        return HttpResponseNotFound("<h2>Catalog not found</h2>")
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Просмотр страницы с информацией о товаре для клиента
#@login_required
def catalog_details(request, id):
    try:
        # Товар с каталога
        catalog = ViewCatalog.objects.get(id=id)
        # Отзывы на данный товар
        review = Review.objects.filter(catalog_id=id).order_by('-date_review')
        question = Question.objects.filter(catalog_id=id).order_by('-date_question')        
        return render(request, "catalog/details.html", {"catalog": catalog, "review": review, "question": question,})
    except Catalog.DoesNotExist:
        return HttpResponseNotFound("<h2>Catalog not found</h2>")

###################################################################################################

# Список для просмотра
def review_list(request):
    try:
        review = Review.objects.all().order_by('-date_review')
        return render(request, "review/list.html", {"review": review})        
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Список для просмотра с кнопкой удалить
@login_required
@group_required("Managers")
def review_index(request):
    try:
        review = Review.objects.all().order_by('-date_review')
        return render(request, "review/index.html", {"review": review})        
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# В функции create() получаем данные из запроса типа POST, сохраняем данные с помощью метода save()
# и выполняем переадресацию на корень веб-сайта (то есть на функцию index).
@login_required
def review_create(request, catalog_id):
    try:
        print(catalog_id)
        catalog = Catalog.objects.get(id=catalog_id)
        if request.method == "POST":
            review = Review()        
            review.catalog_id = catalog_id
            review.rating = request.POST.get("rating")
            review.details = request.POST.get("details")
            review.user = request.user
            reviewform = ReviewForm(request.POST)
            if reviewform.is_valid():
                review.save()
                return HttpResponseRedirect(reverse('catalog_list'))
            else:
                return render(request, "review/create.html", {"form": reviewform,  "catalog_id": catalog_id, })     
        else:        
            reviewform = ReviewForm(initial={'rating': 5, })
            return render(request, "review/create.html", {"form": reviewform, "catalog": catalog, })        
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Удаление данных из бд
# Функция delete аналогичным функции edit образом находит объет и выполняет его удаление.
@login_required
@group_required("Managers")
def review_delete(request, id):
    try:
        review = Review.objects.get(id=id)
        review.delete()
        return HttpResponseRedirect(reverse('review_index'))
    except Review.DoesNotExist:
        return HttpResponseNotFound("<h2>Review not found</h2>")

###################################################################################################

# Список для просмотра
def question_list(request):
    try:
        question = Question.objects.all().order_by('-date_question')
        return render(request, "question/list.html", {"question": question})        
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Список для просмотра с кнопкой удалить
@login_required
@group_required("Managers")
def question_index(request):
    try:
        question = Question.objects.all().order_by('-date_question')
        return render(request, "question/index.html", {"question": question})        
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# В функции create() получаем данные из запроса типа POST, сохраняем данные с помощью метода save()
# и выполняем переадресацию на корень веб-сайта (то есть на функцию index).
@login_required
def question_create(request, catalog_id):
    try:
        print(catalog_id)
        catalog = Catalog.objects.get(id=catalog_id)
        if request.method == "POST":
            question = Question()        
            question.catalog_id = catalog_id
            question.question = request.POST.get("question")
            question.user = request.user
            questionform = QuestionCreateForm(request.POST)
            if questionform.is_valid():
                question.save()
                return HttpResponseRedirect(reverse('catalog_list'))
            else:
                return render(request, "question/create.html", {"form": questionform,  "catalog_id": catalog_id, })     
        else:        
            questionform = QuestionCreateForm(initial={'rating': 5, })
            return render(request, "question/create.html", {"form": questionform, "catalog": catalog, })        
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Функция edit выполняет редактирование объекта.
# Функция в качестве параметра принимает идентификатор объекта в базе данных.
@login_required
@group_required("Managers")
def question_edit(request, id):
    try:
        question = Question.objects.get(id=id) 
        catalog = Catalog.objects.get(id=question.catalog_id)
        if request.method == "POST":
            question.answer = request.POST.get("answer")
            questionform = QuestionEditForm(request.POST)
            if questionform.is_valid():
                question.save()
                return HttpResponseRedirect(reverse('question_index'))
            else:
                return render(request, "question/edit.html", {"form": questionform})            
        else:
            # Загрузка начальных данных
            questionform = QuestionEditForm(initial={'answer': question.answer })
            #print('->',question.photo )
            return render(request, "question/edit.html", {"form": questionform , 'question': question , 'catalog': catalog})
    except Question.DoesNotExist:
        return HttpResponseNotFound("<h2>Question not found</h2>")
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Удаление данных из бд
# Функция delete аналогичным функции edit образом находит объет и выполняет его удаление.
@login_required
@group_required("Managers")
def question_delete(request, id):
    try:
        question = Question.objects.get(id=id)
        question.delete()
        return HttpResponseRedirect(reverse('question_index'))
    except Question.DoesNotExist:
        return HttpResponseNotFound("<h2>Question not found</h2>")

# Просмотр страницы с информацией о товаре для менеджера.
@login_required
@group_required("Managers")
def question_read(request, id):
    try:
        question = Question.objects.get(id=id) 
        return render(request, "question/read.html", {"question": question})
    except Question.DoesNotExist:
        return HttpResponseNotFound("<h2>Question not found</h2>")
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

###################################################################################################

# Список для изменения с кнопками создать, изменить, удалить
@login_required
@group_required("Managers")
def news_index(request):
    try:
        news = News.objects.all().order_by('-daten')
        return render(request, "news/index.html", {"news": news})
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Список для просмотра
def news_list(request):
    try:
        news = News.objects.all().order_by('-daten')
        if request.method == "POST":
            # Определить какая кнопка нажата
            if 'searchBtn' in request.POST:
                # Поиск по названию 
                news_search = request.POST.get("news_search")
                #print(news_search)                
                if news_search != '':
                    news = news.filter(Q(title__contains = news_search) | Q(details__contains = news_search)).all()                
                return render(request, "news/list.html", {"news": news, "news_search": news_search, })    
            else:          
                return render(request, "news/list.html", {"news": news})                 
        else:
            return render(request, "news/list.html", {"news": news}) 
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# В функции create() получаем данные из запроса типа POST, сохраняем данные с помощью метода save()
# и выполняем переадресацию на корень веб-сайта (то есть на функцию index).
@login_required
@group_required("Managers")
def news_create(request):
    try:
        if request.method == "POST":
            news = News()        
            news.daten = request.POST.get("daten")
            news.news_title = request.POST.get("news_title")
            news.details = request.POST.get("details")
            if 'photo' in request.FILES:                
                news.photo = request.FILES['photo']   
            newsform = NewsForm(request.POST)
            if newsform.is_valid():
                news.save()
                return HttpResponseRedirect(reverse('news_index'))
            else:
                return render(request, "news/create.html", {"form": newsform})
        else:        
            newsform = NewsForm(initial={'daten': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), })
            return render(request, "news/create.html", {"form": newsform})
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Функция edit выполняет редактирование объекта.
# Функция в качестве параметра принимает идентификатор объекта в базе данных.
@login_required
@group_required("Managers")
def news_edit(request, id):
    try:
        news = News.objects.get(id=id) 
        if request.method == "POST":
            news.daten = request.POST.get("daten")
            news.news_title = request.POST.get("news_title")
            news.details = request.POST.get("details")
            if "photo" in request.FILES:                
                news.photo = request.FILES["photo"]
            newsform = NewsForm(request.POST)
            if newsform.is_valid():
                news.save()
                return HttpResponseRedirect(reverse('news_index'))
            else:
                return render(request, "news/edit.html", {"form": newsform})
        else:
            # Загрузка начальных данных
            newsform = NewsForm(initial={'daten': news.daten.strftime('%Y-%m-%d %H:%M:%S'), 'news_title': news.news_title, 'details': news.details, 'photo': news.photo })
            return render(request, "news/edit.html", {"form": newsform})
    except News.DoesNotExist:
        return HttpResponseNotFound("<h2>News not found</h2>")
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Удаление данных из бд
# Функция delete аналогичным функции edit образом находит объет и выполняет его удаление.
@login_required
@group_required("Managers")
def news_delete(request, id):
    try:
        news = News.objects.get(id=id)
        news.delete()
        return HttpResponseRedirect(reverse('news_index'))
    except News.DoesNotExist:
        return HttpResponseNotFound("<h2>News not found</h2>")
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Просмотр страницы read.html для просмотра объекта.
#@login_required
def news_read(request, id):
    try:
        news = News.objects.get(id=id) 
        return render(request, "news/read.html", {"news": news})
    except News.DoesNotExist:
        return HttpResponseNotFound("<h2>News not found</h2>")
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

###################################################################################################

# Регистрационная форма 
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('index')
            #return render(request, 'registration/register_done.html', {'new_user': user})
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

# Изменение данных пользователя
@method_decorator(login_required, name='dispatch')
class UserUpdateView(UpdateView):
    model = User
    fields = ('first_name', 'last_name', 'email',)
    template_name = 'registration/my_account.html'
    success_url = reverse_lazy('index')
    #success_url = reverse_lazy('my_account')
    def get_object(self):
        return self.request.user

# Выход
from django.contrib.auth import logout
def logoutUser(request):
    logout(request)
    return render(request, "index.html")

