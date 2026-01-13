from django.contrib import admin
from .models import BasicInformation, WorkPension, InvestmentAccount, LifeEvent


@admin.register(WorkPension)
class WorkPensionAdmin(admin.ModelAdmin):
    list_display = ['id', 'has_pension', 'monthly_pension_amount', 'pension_start_age']


@admin.register(BasicInformation)
class BasicInformationAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'client_id', 'current_age', 'work_optional_age', 'created_at']
    list_filter = ['created_at', 'client_id']
    search_fields = ['client_id', 'user_id']


@admin.register(InvestmentAccount)
class InvestmentAccountAdmin(admin.ModelAdmin):
    list_display = ['id', 'basic_information', 'account_type', 'balance', 'monthly_contribution', 'investment_profile']
    list_filter = ['account_type', 'created_at']
    search_fields = ['account_type', 'investment_profile']


@admin.register(LifeEvent)
class LifeEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'basic_information', 'name', 'event_type', 'frequency', 'amount', 'start_age', 'end_age', 'account']
    list_filter = ['event_type', 'frequency', 'created_at']
    search_fields = ['name', 'account', 'notes']
