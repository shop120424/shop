from django.contrib import admin

# Register your models here.
from .models import Category, Catalog, Review, Question , News 

# Добавление модели на главную страницу интерфейса администратора
admin.site.register(Category)
admin.site.register(Catalog)
admin.site.register(Review)
admin.site.register(Question)
admin.site.register(News)

