from django import forms
from django.forms import ModelForm, TextInput, Textarea, DateInput, NumberInput, DateTimeInput, CheckboxInput
from .models import Category, Catalog, Review, Question, News
#from django.utils.translation import ugettext as _
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
import re
import datetime
from dateutil.relativedelta import relativedelta
from django.utils import timezone
import pytz

# При разработке приложения, использующего базу данных, чаще всего необходимо работать с формами, которые аналогичны моделям.
# В этом случае явное определение полей формы будет дублировать код, так как все поля уже описаны в модели.
# По этой причине Django предоставляет вспомогательный класс, который позволит вам создать класс Form по имеющейся модели
# атрибут fields - указание списка используемых полей, при fields = '__all__' - все поля
# атрибут widgets для указания собственный виджет для поля. Его значением должен быть словарь, ключами которого являются имена полей, а значениями — классы или экземпляры виджетов.

# Категория товара
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_title',]
        widgets = {
            'category_title': TextInput(attrs={"size":"100"}),            
        }

# Товар 
class CatalogForm(forms.ModelForm):
    class Meta:
        model = Catalog
        fields = ('category', 'catalog_title', 'details', 'price', 'photo')
        widgets = {
            'category': forms.Select(attrs={'class': 'chosen'}),
            'catalog_title': TextInput(attrs={"size":"100"}),
            'details': Textarea(attrs={'cols': 100, 'rows': 5}),            
            'price': NumberInput(attrs={"size":"10", "min": "1", "step": "1"}),
        }
    # Метод-валидатор для поля price
    def clean_price(self):
        data = self.cleaned_data['price']
        #print(data)
        # Проверка номер больше нуля
        if data <= 0:
            raise forms.ValidationError(_('Price must be greater than zero'))
        # Метод-валидатор обязательно должен вернуть очищенные данные, даже если не изменил их
        return data       

# Отзывы
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('details', 'rating')
        widgets = {
            'details': Textarea(attrs={'rows': 10}),                        
            'rating': forms.NumberInput(attrs={'max': '5', 'min': '1'}),            
        }

# Вопросы
class QuestionCreateForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('question',)
        widgets = {
            'question': Textarea(attrs={'rows': 7}),                        
        }

class QuestionEditForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('answer',)
        widgets = {
            'answer': Textarea(attrs={'rows': 7}),                        
        }

# Новости
class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ('daten', 'news_title', 'details', 'photo')
        widgets = {
            'daten': DateTimeInput(format='%d/%m/%Y %H:%M:%S'),
            'news_title': TextInput(attrs={"size":"100"}),
            'details': Textarea(attrs={'cols': 100, 'rows': 10}),                        
        }
    # Метод-валидатор для поля daten
    def clean_daten(self):        
        if isinstance(self.cleaned_data['daten'], datetime.date) == True:
            data = self.cleaned_data['daten']
            #print(data)        
        else:
            raise forms.ValidationError(_('Wrong date and time format'))
        # Метод-валидатор обязательно должен вернуть очищенные данные, даже если не изменил их
        return data   

# Форма регистрации
class SignUpForm(UserCreationForm):
    email = forms.CharField(max_length=254, required=True, widget=forms.EmailInput())
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')
