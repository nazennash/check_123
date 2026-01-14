from django.db import models


class BasicInformation(models.Model):
    user_id = models.AutoField(primary_key=True)
    client_id = models.IntegerField(unique=True)
    current_age = models.IntegerField()
    work_optional_age = models.IntegerField(null=True, blank=True)
    yearly_income_for_ideal_lifestyle = models.BigIntegerField(null=True, blank=True)
    inflation_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    return_after_work_optional = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    plan_until_age = models.IntegerField(null=True, blank=True)
    cpp_start_age = models.IntegerField(null=True, blank=True)
    cpp_amount_at_age = models.BigIntegerField(null=True, blank=True)
    oas_start_age = models.IntegerField(null=True, blank=True)
    oas_amount_at_OAS_age = models.BigIntegerField(null=True, blank=True)
    withdrawal_strategy = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'basic_information'


class InvestmentAccount(models.Model):
    basic_information = models.ForeignKey(BasicInformation, on_delete=models.CASCADE, related_name='investment_accounts')
    account_type = models.CharField(max_length=255, null=True, blank=True)
    balance = models.BigIntegerField()
    monthly_contribution = models.BigIntegerField(null=True, blank=True)
    investment_profile = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investment_account'


class LifeEvent(models.Model):
    FREQUENCY_CHOICES = [
        ('one_time', 'One Time'),
        ('monthly', 'Monthly'),
        ('annually', 'Annually'),
    ]
    
    EVENT_TYPE_CHOICES = [
        ('contribution', 'Contribution'),
        ('expenses', 'Expenses'),
    ]
    
    basic_information = models.ForeignKey(BasicInformation, on_delete=models.CASCADE, related_name='life_events')
    name = models.CharField(max_length=255, blank=True, default='')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES, null=True, blank=True)
    frequency = models.CharField(max_length=50, choices=FREQUENCY_CHOICES, default='one_time')
    amount = models.BigIntegerField(default=0)
    start_age = models.IntegerField(default=0)
    end_age = models.IntegerField(default=0)
    account = models.CharField(max_length=255, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'life_event'


class WorkPension(models.Model):
    basic_information = models.ForeignKey(BasicInformation, on_delete=models.CASCADE, related_name='work_pensions')
    has_pension = models.BooleanField(null=True, blank=True)
    monthly_pension_amount = models.BigIntegerField(null=True, blank=True)
    pension_start_age = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'work_pension'
