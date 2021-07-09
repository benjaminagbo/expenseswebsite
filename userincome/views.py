from .models import Source,Income
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
import json
from django.http import JsonResponse
from userpreferences.models import UserPreference
import datetime
# Create your views here.


def search_income(request):
    if request.method=='POST':
        search_str=json.loads(request.body).get('SearchText')
        income=Income.objects.filter(
            amount__istartswith=search_str, owner=request.user)|Income.objects.filter(
            date__istartswith=search_str, owner=request.user)|Income.objects.filter(
            description__icontains=search_str, owner=request.user)|Income.objects.filter(
            source__icontains=search_str, owner=request.user)
        data=income.values()
        return JsonResponse(list(data),safe=False)


@login_required(login_url='/authentication/login')
def index(request):
    sources=Source.objects.all()
    income=Income.objects.filter(owner=request.user)
    paginator=Paginator(income,5)
    page_number=request.GET.get('page')
    currency=UserPreference.objects.get(user=request.user).currency
    page_obj=Paginator.get_page(paginator,page_number)
    context={
        'income':income,
        'page_obj':page_obj,
        'currency':currency
    }
    return render(request,'income/index.html',context)

def add_income(request):
    sources = Source.objects.all()
    context = {
        'sources':sources,
        'values':request.POST
    }
    if request.method=='GET':
        return render(request, 'income/add_income.html', context)
    if request.method == 'POST':
        amount = request.POST['amount']
        if not amount:
            messages.error(request,'Amount is required')
            return render(request, 'income/add_income.html', context)
        description = request.POST['description']
        date = request.POST['income_date']
        source = request.POST['source']
        if not description:
            messages.error(request,'description is required')
            return render(request, 'income/add_income.html', context)
        Income.objects.create(owner=request.user, amount=amount, date=date, source=source, description=description)
        messages.success(request, 'Income saved Successfully!')
        return redirect('income')

#@login_required(login_url='/authentication/login')
def income_edit(request, id):
    income = Income.objects.get(pk=id)
    sources = Source.objects.all()
    context = {
        'income': income,
        'values': income,
        'sources': sources
    }
    if request.method == 'GET':
        return render(request, 'income/edit_income.html', context)
    if request.method == 'POST':
        amount = request.POST['amount']
        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'income/edit_income.html', context)
    description = request.POST['description']
    date = request.POST['income_date']
    source = request.POST['source']
    if not description:
        messages.error(request, 'description is required')
        return render(request, 'income/edit_income.html', context)
    income.owner = request.user
    income.amount = amount
    income.date = date
    income.source = source
    income.description = description
    income.save()
    messages.success(request, 'Income Updated Successfully!')
    return redirect('income')


def delete_income(request, id):
    income = Income.objects.get(pk=id)
    income.delete()
    messages.success(request, 'Income deleted Successfully!')
    return redirect('income')




#/////////////////////////////////////////

def income_source_summary(request):
    todays_date=datetime.date.today()
    six_months_ago=todays_date-datetime.timedelta(days=30*12)
    incomes=Income.objects.filter(owner=request.user, date__gte=six_months_ago, date__lte=todays_date)
    finalrep= {}

    def get_source(income):
        return income.source
    source_list=list(set(map(get_source, incomes)))
    def get_income_source_amount(source):
        amount=0
        filtered_by_source=incomes.filter(source=source)
        for item in filtered_by_source:
            amount+= item.amount
        return amount

    for x in incomes:
        for y in source_list:
            finalrep[y]=get_income_source_amount(y)
    return JsonResponse({'income_source_data': finalrep}, safe=False)


def stats_View_two(request):
    return render(request, 'income/stats.html')





'''

def expense_category_summary(request):
    todays_date=datetime.date.today()
    six_months_ago=todays_date-datetime.timedelta(days=30*12)
    expenses=Expense.objects.filter(owner=request.user, date__gte=six_months_ago, date__lte=todays_date)
    finalrep= {}

    def get_category(expense):
        return expense.category
    category_list=list(set(map(get_category, expenses)))
    def get_expense_category_amount(category):
        amount=0
        filtered_by_category=expenses.filter(category=category)
        for item in filtered_by_category:
            amount+=item.amount
        return amount

    for x in expenses:
        for y in category_list:
            finalrep[y]=get_expense_category_amount(y)
    return JsonResponse({'expense_category_data': finalrep}, safe=False)




def stats_View(request):
    return render(request, 'expenses/stats.html')

'''