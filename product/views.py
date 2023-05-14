from django.shortcuts import render
from django.contrib.auth.decorators import login_required
#from django.utils.translation import ugettext as _
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound

from django.utils.decorators import method_decorator
from django.views.generic import UpdateView
from django.contrib.auth.models import User
from django.urls import reverse_lazy

from django.urls import reverse

from django.contrib.auth import login as auth_login

import datetime

import time

import csv
import xlwt
from io import BytesIO

# Подключение моделей
from django.contrib.auth.models import User, Group

from django.db import models
from django.db.models import Q

# Подключение моделей
from .models import Category, Catalog, ViewCatalog, Basket, Sale, ViewSale, Delivery, News
# Подключение форм
from .forms import CategoryForm, CatalogForm, DeliveryForm, NewsForm, SignUpForm

from django.contrib.auth.models import AnonymousUser

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

# Стартовая страница 
def index(request):
    catalog = ViewCatalog.objects.all().order_by('?')[0:4]
    reviews = ViewSale.objects.exclude(rating=None).order_by('?')[0:4]
    news1 = News.objects.all().order_by('-daten')[0:1]
    news24 = News.objects.all().order_by('-daten')[1:4]
    return render(request, "index.html", {"catalog": catalog, "reviews": reviews, "news1": news1, "news24": news24})    

# Контакты
def contact(request):
    return render(request, "contact.html")

# Отчеты
def report_index(request):
    try:
        catalog = ViewCatalog.objects.all().order_by('title')
        sale = ViewSale.objects.all().order_by('saleday')
        delivery = Delivery.objects.all().order_by('deliveryday')
        review = ViewSale.objects.all().order_by('category', 'title', 'saleday')
        return render(request, "report/index.html", {"catalog": catalog, "sale": sale, "delivery": delivery, "review": review })
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

###################################################################################################
# Список для изменения с кнопками создать, изменить, удалить
@login_required
@group_required("Managers")
def category_index(request):
    try:
        category = Category.objects.all().order_by('title')
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
            category.title = request.POST.get("title")
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
            category.title = request.POST.get("title")
            categoryform = CategoryForm(request.POST)
            if categoryform.is_valid():
                category.save()
                return HttpResponseRedirect(reverse('category_index'))
            else:
                return render(request, "category/edit.html", {"form": categoryform})
        else:
            # Загрузка начальных данных
            categoryform = CategoryForm(initial={'title': category.title, })
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
def category_read(request, id):
    try:
        category = Category.objects.get(id=id) 
        return render(request, "category/read.html", {"category": category})
    except Category.DoesNotExist:
        return HttpResponseNotFound("<h2>Category not found</h2>")
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

###################################################################################################

# Список для изменения с кнопками создать, изменить, удалить
@login_required
@group_required("Managers")
def catalog_index(request):
    try:
        catalog = Catalog.objects.all().order_by('title')
        return render(request, "catalog/index.html", {"catalog": catalog, })
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)
    
# Список для просмотра и отправки в корзину
#@login_required
def catalog_list(request):
    try:
        # Только доступный товар
        catalog = ViewCatalog.objects.order_by('title')
        # Подчситать количество товара в корзине доступны записи только текущего пользователя
        # Текущий пользователь
        _user_id = request.user.id
        basket_count = Basket.objects.filter(user_id=_user_id).count()
        #print(basket_count)        
        if request.method == "POST":
            # Выделить id товара
            catalog_id = request.POST.dict().get("catalog_id")
            #print("catalog_id ", catalog_id)
            price = request.POST.dict().get("price")
            #print("price ", price)
            user = request.POST.dict().get("user")
            #print("user ", user)
            # Отправить товар в корзину
            basket = Basket()
            basket.catalog_id = catalog_id
            basket.price = float(int(price.replace(",00","")))
            #basket.price = price
            basket.user_id = user
            basket.save()
            message = _('Item added to basket')
            basket_count = Basket.objects.filter(user_id=_user_id).count()
            return render(request, "catalog/list.html", {"catalog": catalog, "mess": message, "basket_count": basket_count })
        else:
            return render(request, "catalog/list.html", {"catalog": catalog, "basket_count": basket_count })
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)
    
# Корзина
@login_required
def basket(request):
    try:
        # Текущий пользователь
        _user_id = request.user.id
        # Доступны записи только текущего пользователя
        basket = Basket.objects.filter(user_id=_user_id).order_by('basketday')
        # Подсчитать стоимость товара в корзине
        basket_total = 0
        for b in basket:
            basket_total = basket_total + b.price*b.quantity
        #print(total)        
        # Если это подтверждение какого-либо действия
        if request.method == "POST":        
            # Увеличение или уменьшение количества товара в корзине
            if ('btn_plus' in request.POST) or ('btn_minus' in request.POST):
                # Выделить id записи в корзине и количество товара       
                basket_id = request.POST.dict().get("basket_id")
                quantity = request.POST.dict().get("quantity")
                # Найти запись в корзине
                basket = Basket.objects.get(id=basket_id)
                # Изменить запись в корзине
                if 'btn_plus' in request.POST:
                    basket.quantity = basket.quantity + 1
                if 'btn_minus' in request.POST:
                    if basket.quantity > 1:
                        basket.quantity = basket.quantity - 1
                # Сохранить
                basket.save()
                # Доступны записи только текущего пользователя
                basket = Basket.objects.filter(user_id=_user_id).order_by('basketday')
                # Подсчитать стоимость товара в корзине
                basket_total = 0
                for b in basket:
                    basket_total = basket_total + b.price*b.quantity
                return render(request, "catalog/basket.html", {"basket": basket, "basket_total": basket_total})
            # Приобретение, если нажата кнопка Buy
            if 'buy' in request.POST:
                # Перебрать всю корзину отправить ее в продажи!
                for b in basket:
                    # Добавить в продажи
                    sale = Sale()
                    sale.catalog_id = b.catalog_id
                    sale.price = b.price
                    sale.quantity = b.quantity
                    sale.user_id = b.user_id
                    sale.details = ""
                    #print("Сохранено")
                    sale.save()
                # Очистить корзину
                #print("Корзина очищена")
                basket.delete()
                # Перейти к совершенным покупкам
                return HttpResponseRedirect(reverse("buy"))
        else:
            return render(request, "catalog/basket.html", {"basket": basket, "basket_total": basket_total})
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Удаление из корзины
@login_required
def basket_delete(request, id):
    try:
        basket = Basket.objects.get(id=id)                
        basket.delete()
        # Текущий пользователь
        _user_id = request.user.id
        # Доступны записи только текущего пользователя
        basket = Basket.objects.filter(user_id=_user_id).order_by('basketday')
        # Подсчитать стоимость товара в корзине
        basket_total = 0
        for b in basket:
            basket_total = basket_total + b.price*b.quantity    
        return render(request, "catalog/basket.html", {"basket": basket, "basket_total": basket_total})
    except Catalog.DoesNotExist:
        return HttpResponseNotFound("<h2>Basket not found</h2>")
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)
    
# Список приобретения + Оставление отзыва
@login_required
def buy(request):
    try:
        # Текущий пользователь
        _user_id = request.user.id
        print(_user_id)
        # Доступны записи только текущего пользователя
        sale = Sale.objects.filter(user_id=_user_id).order_by('saleday')    
        # Если это подтверждение какого-либо действия
        if request.method == "POST":
            # Отправить отзыв, если нажата кнопка Review
            if 'review' in request.POST:
                # Выделить id записи в таблице sale        
                sale_id = request.POST.dict().get("sale_id")
                review = Sale.objects.get(id=sale_id) 
                review.rating = request.POST.dict().get("rating")
                review.details = request.POST.dict().get("rating_details")
                #print(sale_id)
                #print(review.rating)
                #print(review.details)
                review.save()            
                return render(request, "catalog/buy.html", {"sale": sale})
        else:
            return render(request, "catalog/buy.html", {"sale": sale})
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
            catalog.title = request.POST.get("title")
            catalog.details = request.POST.get("details")        
            catalog.price = request.POST.get("price")
            catalog.quantity = request.POST.get("quantity")
            if 'photo' in request.FILES:                
                catalog.photo = request.FILES['photo']
            catalogform = CatalogForm(request.POST)
            if catalogform.is_valid():
                catalog.save()
                return HttpResponseRedirect(reverse('catalog_index', ))
            else:
                return render(request, "catalog/create.html", {"form": catalogform})
        else:        
            catalogform = CatalogForm()
            return render(request, "catalog/create.html", {"form": catalogform, })
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Функция edit выполняет редактирование объекта.
@login_required
@group_required("Managers")
def catalog_edit(request, id):
    try:
        catalog = Catalog.objects.get(id=id) 
        if request.method == "POST":
            catalog.category = Category.objects.filter(id=request.POST.get("category")).first()
            catalog.title = request.POST.get("title")
            catalog.details = request.POST.get("details")        
            catalog.price = request.POST.get("price")
            catalog.quantity = request.POST.get("quantity")
            if 'photo' in request.FILES:
                catalog.photo = request.FILES['photo']
            catalogform = CatalogForm(request.POST)
            if catalogform.is_valid():
                catalog.save()
                return HttpResponseRedirect(reverse('catalog_index', ))
            else:
                return render(request, "catalog/edit.html", {"form": catalogform, })            
        else:
            # Загрузка начальных данных
            catalogform = CatalogForm(initial={'category': catalog.category, 'title': catalog.title, 'details': catalog.details, 'price': catalog.price, 'photo': catalog.photo, })
            #print('->',catalog.photo )
            return render(request, "catalog/edit.html", {"form": catalogform, })
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
        return HttpResponseRedirect(reverse('catalog_index', ))
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
        catalog = Catalog.objects.get(id=id) 
        return render(request, "catalog/read.html", {"catalog": catalog, })
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
        reviews = ViewSale.objects.filter(catalog_id=id).exclude(rating=None)
        return render(request, "catalog/details.html", {"catalog": catalog, "reviews": reviews,})
    except Catalog.DoesNotExist:
        return HttpResponseNotFound("<h2>Catalog not found</h2>")

###################################################################################################
#    
# Список продаж с указанием последнего движения в доставке
@login_required
def delivery_list(request):    
    try:
        if request.user.groups.filter(name='Managers').exists():
            view_sale = ViewSale.objects.all().order_by('-saleday')        
        else:
            _user_id = request.user.id
            view_sale = ViewSale.objects.filter(user_id=_user_id).order_by('-saleday')        
        return render(request, "delivery/list.html", {"view_sale": view_sale})
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)
    
# Список для изменения с кнопками создать, изменить, удалить для конкретной доставки
@login_required
def delivery_index(request, id):
    try:
        delivery = Delivery.objects.filter(sale_id=id)
        view_sale = ViewSale.objects.get(id=id)
        return render(request, "delivery/index.html", {"delivery": delivery, "view_sale": view_sale})
    except Delivery.DoesNotExist:
        return HttpResponseNotFound("<h2>Delivery not found</h2>")

# В функции create() получаем данные из запроса типа POST, сохраняем данные с помощью метода save()
# и выполняем переадресацию на корень веб-сайта (то есть на функцию index).
@login_required
@group_required("Managers")
def delivery_create(request, sale_id):
    try:
        if request.method == "POST":
            delivery = Delivery()
            delivery.sale_id = sale_id
            delivery.deliveryday = request.POST.get("deliveryday")
            delivery.movement = request.POST.get("movement")
            delivery.details = request.POST.get("details")
            deliveryform = DeliveryForm(request.POST)
            if deliveryform.is_valid():
                delivery.save()
                return HttpResponseRedirect(reverse('delivery_index', args=(delivery.sale_id,)))
            else:
                return render(request, "delivery/create.html", {"form": deliveryform})
        else:
            deliveryform = DeliveryForm()
            return render(request, "delivery/create.html/", {"form": deliveryform, 'sale_id': sale_id,})
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Функция edit выполняет редактирование объекта.
@login_required
@group_required("Managers")
def delivery_edit(request, id):
    try:
        delivery = Delivery.objects.get(id=id) 
        if request.method == "POST":
            delivery.movement = request.POST.get("movement")
            delivery.details = request.POST.get("details")
            deliveryform = DeliveryForm(request.POST)
            if deliveryform.is_valid():
                delivery.save()
                return HttpResponseRedirect(reverse('delivery_index', args=(delivery.sale_id,)))
            else:
                return render(request, "delivery/edit.html", {"form": deliveryform})
        else:
            # Загрузка начальных данных
            deliveryform = DeliveryForm(initial={'sale': delivery.sale, 'deliveryday': delivery.deliveryday, 'movement': delivery.movement, 'details': delivery.details,})
            return render(request, "delivery/edit.html", {"form": deliveryform, 'sale_id': delivery.sale_id, })
    except Delivery.DoesNotExist:
        return HttpResponseNotFound("<h2>Delivery not found</h2>")
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Удаление данных из бд
# Функция delete аналогичным функции edit образом находит объет и выполняет его удаление.
@login_required
@group_required("Managers")
def delivery_delete(request, id):
    try:
        delivery = Delivery.objects.get(id=id)
        delivery.delete()
        return HttpResponseRedirect(reverse('delivery_index', args=(delivery.sale_id,)))
    except Delivery.DoesNotExist:
        return HttpResponseNotFound("<h2>Delivery not found</h2>")
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Просмотр страницы read.html для просмотра объекта.
@login_required
def delivery_read(request, id):
    try:
        delivery = Delivery.objects.get(id=id) 
        return render(request, "delivery/read.html", {"delivery": delivery, "sale_id": delivery.sale_id})
    except Catalog.DoesNotExist:
        return HttpResponseNotFound("<h2>Catalog not found</h2>")
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)
   
###################################################################################################

# Список для изменения с кнопками создать, изменить, удалить
@login_required
@group_required("Managers")
def news_index(request):
    try:
        #news = News.objects.all().order_by('surname', 'name', 'patronymic')
        #return render(request, "news/index.html", {"news": news})
        news = News.objects.all().order_by('-daten')
        return render(request, "news/index.html", {"news": news})
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)


# Список для просмотра
def news_list(request):
    try:
        news = News.objects.all().order_by('-daten')
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
            news.title = request.POST.get("title")
            news.details = request.POST.get("details")
            if 'photo' in request.FILES:                
                news.photo = request.FILES['photo']        
            news.save()
            return HttpResponseRedirect(reverse('news_index'))
        else:        
            #newsform = NewsForm(request.FILES, initial={'daten': datetime.datetime.now().strftime('%Y-%m-%d'),})
            newsform = NewsForm(initial={'daten': datetime.datetime.now().strftime('%Y-%m-%d'), })
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
            news.title = request.POST.get("title")
            news.details = request.POST.get("details")
            if "photo" in request.FILES:                
                news.photo = request.FILES["photo"]
            news.save()
            return HttpResponseRedirect(reverse('news_index'))
        else:
            # Загрузка начальных данных
            newsform = NewsForm(initial={'daten': news.daten.strftime('%Y-%m-%d'), 'title': news.title, 'details': news.details, 'photo': news.photo })
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
    try:
        if request.method == 'POST':
            form = SignUpForm(request.POST)
            if form.is_valid():
                user = form.save()
                auth_login(request, user)
                return HttpResponseRedirect(reverse('index'))
                #return render(request, 'registration/register_done.html', {'new_user': user})
        else:
            form = SignUpForm()
        return render(request, 'registration/signup.html', {'form': form})
    except Exception as exception:
        print(exception)
        return HttpResponse(exception)

# Изменение данных пользователя
@method_decorator(login_required, name='dispatch')
class UserUpdateView(UpdateView):
    try:
        model = User
        fields = ('first_name', 'last_name', 'email',)
        template_name = 'registration/my_account.html'
        success_url = reverse_lazy('index')
        #success_url = reverse_lazy('my_account')
        def get_object(self):
            return self.request.user
    except Exception as exception:
        print(exception)



