from django.contrib import admin
from .models import BasicInformation, WorkPension, InvestmentAccount, LifeEvent


@admin.register(WorkPension)
class WorkPensionAdmin(admin.ModelAdmin):
    list_display = ['id', 'basic_information', 'client_id', 'has_pension', 'monthly_pension_amount', 'pension_start_age', 'created_at']
    list_filter = ['has_pension', 'pension_start_age', 'created_at']
    search_fields = ['basic_information__client_id', 'basic_information__user_id']
    list_select_related = ['basic_information']  # Optimize queries
    
    def client_id(self, obj):
        """Display client_id for easier filtering"""
        return obj.basic_information.client_id if obj.basic_information else None
    client_id.short_description = 'Client ID'
    client_id.admin_order_field = 'basic_information__client_id'


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
