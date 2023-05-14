from django.db import models
#from django.utils.translation import ugettext as _
from django.utils.translation import gettext_lazy as _
from PIL import Image
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

from django.contrib.auth.models import User

# Модели отображают информацию о данных, с которыми вы работаете.
# Они содержат поля и поведение ваших данных.
# Обычно одна модель представляет одну таблицу в базе данных.
# Каждая модель это класс унаследованный от django.db.models.Model.
# Атрибут модели представляет поле в базе данных.
# Django предоставляет автоматически созданное API для доступа к данным

# choices (список выбора). Итератор (например, список или кортеж) 2-х элементных кортежей,
# определяющих варианты значений для поля.
# При определении, виджет формы использует select вместо стандартного текстового поля
# и ограничит значение поля указанными значениями.

# Категория товара
class Category(models.Model):
    # Читабельное имя поля (метка, label). Каждое поле, кроме ForeignKey, ManyToManyField и OneToOneField,
    # первым аргументом принимает необязательное читабельное название.
    # Если оно не указано, Django самостоятельно создаст его, используя название поля, заменяя подчеркивание на пробел.
    # null - Если True, Django сохранит пустое значение как NULL в базе данных. По умолчанию - False.
    # blank - Если True, поле не обязательно и может быть пустым. По умолчанию - False.
    # Это не то же что и null. null относится к базе данных, blank - к проверке данных.
    # Если поле содержит blank=True, форма позволит передать пустое значение.
    # При blank=False - поле обязательно.
    title = models.CharField(_('category_title'), max_length=128, unique=True)
    class Meta:
        # Параметры модели
        # Переопределение имени таблицы
        db_table = 'category'
    def __str__(self):
        # Вывод названияв тег SELECT 
        return "{}".format(self.title)

# Каталог товаров
class Catalog(models.Model):
    category = models.ForeignKey(Category, related_name='catalog_category', on_delete=models.CASCADE)
    title = models.CharField(_('catalog_title'), max_length=255)
    details = models.TextField(_('catalog_details'), blank=True, null=True)
    price = models.DecimalField(_('price'), max_digits=9, decimal_places=2)
    photo = models.ImageField(_('photo'), upload_to='images/', blank=True, null=True)
    class Meta:
        # Параметры модели
        # Переопределение имени таблицы
        db_table = 'catalog'
        # indexes - список индексов, которые необходимо определить в модели
        indexes = [
            models.Index(fields=['title']),
        ]
        # Сортировка по умолчанию
        ordering = ['title']
    def __str__(self):
        # Вывод в тег SELECT 
        return "{} {} {}".format(self.category, self.title, self.price)

# Представление базы данных Каталог товаров (со средней оценкой)
class ViewCatalog(models.Model):
    category_id = models.IntegerField(_('category_id'))
    category = models.CharField(_('category_title'), max_length=128)
    title = models.CharField(_('catalog_title'), max_length=255)
    details = models.TextField(_('catalog_details'), blank=True, null=True)
    price = models.DecimalField(_('price'), max_digits=9, decimal_places=2)
    photo = models.ImageField(_('photo'), upload_to='images/', blank=True, null=True)
    avg_rating = models.DecimalField(_('avg_rating'), max_digits=6, decimal_places=2)
    class Meta:
        # Параметры модели
        # Переопределение имени таблицы
        db_table = 'view_catalog'
        # indexes - список индексов, которые необходимо определить в модели
        indexes = [
            models.Index(fields=['title']),
        ]
        # Сортировка по умолчанию
        ordering = ['title']
        # Таблицу не надо не добавлять не удалять
        managed = False

# Корзина 
class Basket(models.Model):
    basketday = models.DateTimeField(_('basketday'), auto_now_add=True)
    catalog = models.ForeignKey(Catalog, related_name='basket_catalog', on_delete=models.CASCADE)
    price = models.DecimalField(_('price'), max_digits=9, decimal_places=2)
    quantity = models.IntegerField(_('quantity'), default=1)
    user = models.ForeignKey(User, related_name='basket_user', on_delete=models.CASCADE)
    class Meta:
        # Параметры модели
        # Переопределение имени таблицы
        db_table = 'basket'
        # indexes - список индексов, которые необходимо определить в модели
        indexes = [
            models.Index(fields=['basketday']),
        ]
        # Сортировка по умолчанию
        ordering = ['basketday']
    # Сумма по товару
    def total(self):
        return self.price * self.quantity

# Продажа 
class Sale(models.Model):
    saleday = models.DateTimeField(_('saleday'), auto_now_add=True)
    catalog = models.ForeignKey(Catalog, related_name='sale_catalog', on_delete=models.CASCADE)
    price = models.DecimalField(_('price'), max_digits=9, decimal_places=2)
    quantity = models.IntegerField(_('quantity'), default=1)
    user = models.ForeignKey(User, related_name='sale_user', on_delete=models.CASCADE)
    rating = models.IntegerField(_('rating'), blank=True, null=True)
    details = models.TextField(_('review_details'), blank=True, null=True)
    class Meta:
        # Параметры модели
        # Переопределение имени таблицы
        db_table = 'sale'
        # indexes - список индексов, которые необходимо определить в модели
        indexes = [
            models.Index(fields=['saleday']),
        ]
        # Сортировка по умолчанию
        ordering = ['saleday']
    # Сумма по товару
    def total(self):
        return self.price * self.quantity
    def __str__(self):
        # Вывод в тег SELECT 
        return "{} {} {}".format(self.saleday.strftime('%d.%m.%Y %H:%M:%S'), self.catalog, self.user.username)

# Представление базы данных Продажа (с последним движением по доставке)
# CREATE VIEW view_sale AS
# SELECT sale.id, username, saleday, catalog_id, view_catalog.category, view_catalog.title, info, code, sale.price, quantity, sale.price*quantity AS total, user_id, rating, sale.details,
# (SELECT strftime('%d.%m.%Y',deliveryday) || ' - ' || movement FROM delivery WHERE sale_id = sale.id AND deliveryday = (SELECT MAX(deliveryday) AS Expr1 FROM delivery AS S WHERE  (sale_id = sale.id) )) AS final
# FROM sale LEFT JOIN view_catalog ON sale.catalog_id = view_catalog.id
# LEFT JOIN auth_user ON sale.user_id = auth_user.id
class ViewSale(models.Model):
    username = models.CharField(_('username'), max_length=128)
    saleday = models.DateTimeField(_('saleday'))
    catalog_id = models.IntegerField(_('catalog_id'))
    category = models.CharField(_('category'), max_length=128)
    title = models.CharField(_('catalog_title'), max_length=255)    
    photo = models.ImageField(_('photo'), upload_to='images/', blank=True, null=True)
    price = models.DecimalField(_('price'), max_digits=9, decimal_places=2)
    quantity = models.IntegerField(_('quantity'))
    total = models.DecimalField(_('total'), max_digits=9, decimal_places=2)
    user_id = models.IntegerField(_('user_id'))
    rating = models.IntegerField(_('rating'), blank=True, null=True)
    details = models.TextField(_('review_details'), blank=True, null=True)
    final = models.TextField(_('final'), blank=True, null=True)
    class Meta:
        # Параметры модели
        # Переопределение имени таблицы
        db_table = 'view_sale'
        # indexes - список индексов, которые необходимо определить в модели
        indexes = [
            models.Index(fields=['saleday']),
        ]
        # Сортировка по умолчанию
        ordering = ['saleday']
        # Таблицу не надо не добавлять не удалять
        managed = False
    # Сумма по товару
    def total(self):
        return self.price * self.quantity
    #def __str__(self):
    #    return "{} {} {}".format(self.category, self.title, self.username)

# Доставка товара
class Delivery(models.Model):
    DELIVERY_CHOICES = (
        (_('Application accepted for processing'),_('Application accepted for processing')),
        (_('Goods in transit'), _('Goods in transit')),
        (_('The application is closed, the goods have been delivered'), _('The application is closed, the goods have been delivered')),
    )
    sale = models.ForeignKey(Sale, related_name='sale_delivery', on_delete=models.CASCADE)    
    deliveryday = models.DateTimeField(_('deliveryday'), auto_now_add=True)
    movement = models.CharField(_('movement'), max_length=64, choices=DELIVERY_CHOICES, default='М')
    details = models.TextField(_('delivery_details'), blank=True, null=True) 
    class Meta:
        # Параметры модели
        # Переопределение имени таблицы
        db_table = 'delivery'
        # indexes - список индексов, которые необходимо определить в модели
        indexes = [
            models.Index(fields=['deliveryday']),
        ]
        # Сортировка по умолчанию
        ordering = ['deliveryday']
    def __str__(self):
        # Вывод в тег SELECT 
        return "{} {} {}".format(self.deliveryday.strftime('%d.%m.%Y %H:%M:%S'), self.sale, self.movement)


# Ќовости 
class News(models.Model):
    daten = models.DateTimeField(_('daten'))
    title = models.CharField(_('title_news'), max_length=256)
    details = models.TextField(_('details_news'))
    photo = models.ImageField(_('photo_news'), upload_to='images/', blank=True, null=True)    
    class Meta:
        # ѕараметры модели
        # ѕереопределение имени таблицы
        db_table = 'news'
        # indexes - список индексов, которые необходимо определить в модели
        indexes = [
            models.Index(fields=['daten']),
        ]
        # —ортировка по умолчанию
        ordering = ['daten']
    #def save(self):
    #    super().save()
    #    img = Image.open(self.photo.path) # Open image
    #    # resize image
    #    if img.width > 512 or img.height > 700:
    #        proportion_w_h = img.width/img.height  # ќтношение ширины к высоте 
    #        output_size = (512, int(512/proportion_w_h))
    #        img.thumbnail(output_size) # »зменение размера
    #        img.save(self.photo.path) # —охранение
