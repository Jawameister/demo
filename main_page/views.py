from django.shortcuts import render, redirect
from . import models
import telebot
import requests

from django.http import HttpResponse
# Create your views here.
def index_page(request):
    # если отправляет отзыв
    if request.method == 'POST':
        mail = request.POST.get('mail')
        feedback = request.POST.get('message')
        models.Feedback.objects.create(user_mail=mail, feedback_message=feedback)
    connect = requests.get(url='https://cbu.uz/ru/arkhiv-kursov-valyut/json/').json()
    products = models.Product.objects.all()
    categories = models.Category.objects.all()
    sales = models.Sale.objects.all()
    currency_rate = connect[0]['Rate']
    weather = "+32 C"

    return render(request, 'index.html', {'products':products,
                                          'categories':categories,
                                          'sales':sales,
                                          'rate': currency_rate})

#Функция поиска
def search_product(request):
    if request.method == 'POST':
        user_search_product = request.POST.get('search')
        try:
            result_product = models.Product.objects.get(product_name=user_search_product)
            return render(request, 'current_product.html', {'result_product': result_product})
        except:
            return redirect('/')

# Получить определенный продутк
def current_product(request, name, pk):
    product = models.Product.objects.get(product_name=name, id=pk)

    return render(request, 'current_product.html', {'result_product': product})


def get_current_category(request, pk):
    current_category = models.Category.objects.get(id=pk)
    products_from_category = models.Product.objects.filter(product_category=current_category)
    return render(request, 'current_category.html', {'products_form_category': products_from_category})

def add_product_to_user_cart(request, pk):
    if request.method == 'POST':
        product = models.Product.objects.get(id=pk)
        product_count = int(request.POST.get("count"))
        user = models.Cart(user_id=request.user.id,
                           user_product=product,
                           product_quantity=product_count,
                           total_for_current_product=product_count*product.product_price)
        product.product_quantity -= product_count
        product.save()
        user.save()

    return redirect('/')

def show_user_cart(request):
    user_cart = models.Cart.objects.filter(user_id=request.user.id)
    total = sum([i.total_for_current_product for i in user_cart])
    return render(request, 'user_cart.html', {'user_cart': user_cart,
                                              'total': total})

def delete_product_from_cart(request, pk):
    if request.method == 'POST':
        product_to_delete = models.Cart.objects.get(id=pk, user_id=request.user.id)
        product = models.Product.objects.get(product_name=product_to_delete.user_product)
        product.product_quantity += product_to_delete.product_quantity
        product_to_delete.delete()
        return redirect('/user_cart')


## Оформление заказа
def confirm_order(request):
    if request.method == 'POST':
        current_user_cart = models.Cart.objects.filter(user_id=request.user.id)
        #Получаем все значения из front части
        client_name = request.POST.get('client_name')
        client_address = request.POST.get('client_address')
        client_number = request.POST.get('client_number')
        client_comment = request.POST.get('client_comment')

        #Формулироввка сообщения для админа в тг
        full_message = f'Новый заказ(из сайта)\n\nИмя: {client_name}' \
                       f'\nАдрес: {client_address}' \
                       f'\nНомер телефона: {client_number}' \
                       f'\nКомментарий к заказу: {client_comment}\n\n'
        for i in current_user_cart:
            full_message += f'Продукт: {i.user_product}\n' \
                            f'Количество: {i.product_quantity}\n' \
                            f'Сумма: {i.total_for_current_product} сум\n\n'
        #Отправка сообщения админу
        bot = telebot.TeleBot('156527573:AAEGt1EAoJsm0mXZ4FbQQNkJmJGpR9wp6iI')
        bot.send_message(95057467, full_message)
        return redirect('/')
