from rest_framework import serializers
from .models import BasicInformation, WorkPension, InvestmentAccount, LifeEvent


class MonteCarloConfigurationSerializer(serializers.Serializer):
    """Serializer for Monte Carlo simulation configuration."""
    num_simulations = serializers.IntegerField(required=True)
    market_volatility = serializers.ChoiceField(
        choices=['conservative', 'high_volatility', 'historical'],
        required=True
    )
    expected_annual_return = serializers.FloatField(required=True)
    standard_deviation = serializers.FloatField(required=True)
    inflation_rate = serializers.FloatField(required=True)
    sequence_of_returns_risk = serializers.ChoiceField(
        choices=['enabled', 'disabled'],
        required=True
    )
    
    def validate_num_simulations(self, value):
        if value not in [5000, 10000, 25000]:
            raise serializers.ValidationError(
                "num_simulations must be one of: 5000, 10000, or 25000"
            )
        return value
    
    def validate_expected_annual_return(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "expected_annual_return must be between 0 and 100"
            )
        return value
    
    def validate_standard_deviation(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "standard_deviation must be between 0 and 100"
            )
        return value
    
    def validate_inflation_rate(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "inflation_rate must be between 0 and 100"
            )
        return value


class WorkPensionSerializer(serializers.ModelSerializer):
    monthly_pension_amount = serializers.DecimalField(max_digits=20, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model = WorkPension
        fields = ['has_pension', 'monthly_pension_amount', 'pension_start_age']

    def validate(self, data):
        has_pension = data.get('has_pension')
        monthly_pension_amount = data.get('monthly_pension_amount')
        pension_start_age = data.get('pension_start_age')
        
        if has_pension is False:
            if monthly_pension_amount is not None:
                raise serializers.ValidationError({
                    'monthly_pension_amount': 'monthly_pension_amount must be null when has_pension is false.'
                })
            if pension_start_age is not None:
                raise serializers.ValidationError({
                    'pension_start_age': 'pension_start_age must be null when has_pension is false.'
                })
        elif has_pension is True:
            if monthly_pension_amount is None:
                raise serializers.ValidationError({
                    'monthly_pension_amount': 'monthly_pension_amount is required when has_pension is true.'
                })
            if pension_start_age is None:
                raise serializers.ValidationError({
                    'pension_start_age': 'pension_start_age is required when has_pension is true.'
                })
        
        return data

    def validate_monthly_pension_amount(self, value):
        if value is not None:
            if value < 0:
                raise serializers.ValidationError("Monthly pension amount cannot be negative.")
            if value > 20000:
                raise serializers.ValidationError("Monthly pension amount cannot exceed $20,000.00.")
        return value

    def validate_pension_start_age(self, value):
        if value is not None:
            if value < 40:
                raise serializers.ValidationError("Pension start age must be at least 40.")
            if value > 75:
                raise serializers.ValidationError("Pension start age cannot exceed 75.")
        return value


class InvestmentAccountSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=20, decimal_places=2)
    monthly_contribution = serializers.DecimalField(max_digits=20, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model = InvestmentAccount
        fields = ['account_type', 'balance', 'monthly_contribution', 'investment_profile']

    def validate_balance(self, value):
        if value is None:
            raise serializers.ValidationError("balance field is required.")
        if value < 0:
            raise serializers.ValidationError("Balance cannot be negative.")
        return value

    def validate_monthly_contribution(self, value):
        if value is not None:
            if value < 0:
                raise serializers.ValidationError("Monthly contribution cannot be negative.")
            if value > 2000:
                raise serializers.ValidationError("Monthly contribution cannot exceed $2,000.00.")
        return value


class LifeEventSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        model = LifeEvent
        fields = ['name', 'event_type', 'frequency', 'amount', 'start_age', 'end_age', 'account', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_age = self.context.get('current_age') if hasattr(self, 'context') and self.context else None

    def validate_frequency(self, value):
        if value is None:
            raise serializers.ValidationError("frequency field is required.")
        valid_frequencies = ['one_time', 'monthly', 'annually']
        if value not in valid_frequencies:
            raise serializers.ValidationError(f"Frequency must be one of: {', '.join(valid_frequencies)}")
        return value

    def validate_event_type(self, value):
        if value is not None:
            valid_types = ['contribution', 'expenses']
            if value not in valid_types:
                raise serializers.ValidationError(f"Event type must be one of: {', '.join(valid_types)}")
        return value

    def validate_amount(self, value):
        if value is None:
            raise serializers.ValidationError("amount field is required.")
        if value < 0.01:
            raise serializers.ValidationError("Amount must be at least $0.01.")
        return value

    def validate_start_age(self, value):
        if value is None:
            raise serializers.ValidationError("start_age field is required.")
        if self.current_age is not None and value < self.current_age:
            raise serializers.ValidationError(f"start_age must be at least {self.current_age} (current_age).")
        if value > 120:
            raise serializers.ValidationError("start_age cannot exceed 120.")
        return value

    def validate_end_age(self, value):
        if value is None:
            raise serializers.ValidationError("end_age field is required.")
        if value > 120:
            raise serializers.ValidationError("end_age cannot exceed 120.")
        return value

    def validate(self, data):
        start_age = data.get('start_age')
        end_age = data.get('end_age')
        if start_age is not None and end_age is not None:
            if end_age <= start_age:
                raise serializers.ValidationError("end_age must be greater than start_age.")
        return data


class BasicInformationSerializer(serializers.ModelSerializer):
    has_work_pension = WorkPensionSerializer(required=False, allow_null=True)
    investment_accounts = InvestmentAccountSerializer(many=True, required=False)
    yearly_income_for_ideal_lifestyle = serializers.DecimalField(max_digits=20, decimal_places=2, required=False, allow_null=True)
    cpp_amount_at_age = serializers.DecimalField(max_digits=20, decimal_places=2, required=False, allow_null=True)
    oas_amount_at_OAS_age = serializers.DecimalField(max_digits=20, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model = BasicInformation
        fields = [
            'user_id',
            'client_id',
            'current_age',
            'work_optional_age',
            'yearly_income_for_ideal_lifestyle',
            'inflation_rate',
            'return_after_work_optional',
            'plan_until_age',
            'cpp_start_age',
            'cpp_amount_at_age',
            'oas_start_age',
            'oas_amount_at_OAS_age',
            'has_work_pension',
            'withdrawal_strategy',
            'investment_accounts'
        ]
        read_only_fields = ['user_id']

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        current_age = ret.get('current_age')
        
        if 'life_events' in data and current_age is not None:
            life_events_data = data.get('life_events', [])
            validated_life_events = []
            errors_list = []
            
            for idx, event_data in enumerate(life_events_data):
                event_serializer = LifeEventSerializer(data=event_data, context={'current_age': current_age})
                if not event_serializer.is_valid():
                    errors_list.append(event_serializer.errors)
                else:
                    validated_life_events.append(event_serializer.validated_data)
            
            if errors_list:
                raise serializers.ValidationError({
                    'life_events': errors_list
                })
            
            ret['life_events'] = validated_life_events
        
        return ret

    def validate_client_id(self, value):
        if value is None:
            raise serializers.ValidationError("client_id field is required.")
        if value < 0:
            raise serializers.ValidationError("client_id cannot be negative.")
        return value

    def validate_current_age(self, value):
        if value is None:
            raise serializers.ValidationError("current_age field is required.")
        if value < 18:
            raise serializers.ValidationError("current_age must be at least 18.")
        if value > 100:
            raise serializers.ValidationError("current_age cannot exceed 100.")
        return value

    def validate_work_optional_age(self, value):
        if value is not None:
            if value < 40:
                raise serializers.ValidationError("work_optional_age must be at least 40.")
            if value > 75:
                raise serializers.ValidationError("work_optional_age cannot exceed 75.")
        return value

    def validate(self, data):
        current_age = data.get('current_age')
        work_optional_age = data.get('work_optional_age')
        plan_until_age = data.get('plan_until_age')
        
        if current_age is not None and work_optional_age is not None:
            if work_optional_age < current_age:
                raise serializers.ValidationError({
                    'work_optional_age': f'work_optional_age ({work_optional_age}) must be greater than or equal to current_age ({current_age}).'
                })
        
        if work_optional_age is not None and plan_until_age is not None:
            if plan_until_age < work_optional_age:
                raise serializers.ValidationError({
                    'plan_until_age': f'plan_until_age ({plan_until_age}) must be greater than or equal to work_optional_age ({work_optional_age}).'
                })
        
        return data

    def validate_yearly_income_for_ideal_lifestyle(self, value):
        if value is not None:
            if value < 10000:
                raise serializers.ValidationError("Yearly income for ideal lifestyle must be at least $10,000.00.")
            if value > 200000:
                raise serializers.ValidationError("Yearly income for ideal lifestyle cannot exceed $200,000.00.")
        return value

    def validate_inflation_rate(self, value):
        if value is not None:
            if value < 0:
                raise serializers.ValidationError("Inflation rate cannot be negative.")
            if value > 10:
                raise serializers.ValidationError("Inflation rate cannot exceed 10%.")
        return value

    def validate_return_after_work_optional(self, value):
        if value is not None:
            if value < 0:
                raise serializers.ValidationError("Return after work optional cannot be negative.")
            if value > 10:
                raise serializers.ValidationError("Return after work optional cannot exceed 10%.")
        return value

    def validate_plan_until_age(self, value):
        if value is not None:
            if value < 0:
                raise serializers.ValidationError("plan_until_age cannot be negative.")
        return value

    def validate_cpp_start_age(self, value):
        if value is not None:
            if value < 60:
                raise serializers.ValidationError("cpp_start_age must be at least 60.")
            if value > 70:
                raise serializers.ValidationError("cpp_start_age cannot exceed 70.")
        return value

    def validate_cpp_amount_at_age(self, value):
        if value is not None:
            if value < 0:
                raise serializers.ValidationError("CPP amount cannot be negative.")
            if value > 50000:
                raise serializers.ValidationError("CPP amount cannot exceed $50,000.00.")
        return value

    def validate_oas_start_age(self, value):
        if value is not None:
            if value < 65:
                raise serializers.ValidationError("oas_start_age must be at least 65.")
            if value > 70:
                raise serializers.ValidationError("oas_start_age cannot exceed 70.")
        return value

    def validate_oas_amount_at_OAS_age(self, value):
        if value is not None:
            if value < 0:
                raise serializers.ValidationError("OAS amount cannot be negative.")
            if value > 50000:
                raise serializers.ValidationError("OAS amount cannot exceed $50,000.00.")
        return value

    def validate_withdrawal_strategy(self, value):
        if value:
            valid_strategies = ['optimized', 'rrsp', 'non_registered', 'tfsa']
            if value not in valid_strategies:
                raise serializers.ValidationError(
                    f"withdrawal_strategy must be one of: {', '.join(valid_strategies)}"
                )
        return value

    def create(self, validated_data):
        has_work_pension_data = validated_data.pop('has_work_pension', None)
        investment_accounts_data = validated_data.pop('investment_accounts', [])
        life_events_data = validated_data.pop('life_events', [])
        
        yearly_income = validated_data.get('yearly_income_for_ideal_lifestyle')
        if yearly_income is not None:
            validated_data['yearly_income_for_ideal_lifestyle'] = int(float(yearly_income) * 100)
        
        cpp_amount = validated_data.get('cpp_amount_at_age')
        if cpp_amount is not None:
            validated_data['cpp_amount_at_age'] = int(float(cpp_amount) * 100)
        
        oas_amount = validated_data.get('oas_amount_at_OAS_age')
        if oas_amount is not None:
            validated_data['oas_amount_at_OAS_age'] = int(float(oas_amount) * 100)
        
        basic_info = BasicInformation.objects.create(**validated_data)
        
        if has_work_pension_data:
            monthly_pension = has_work_pension_data.get('monthly_pension_amount')
            if monthly_pension is not None:
                has_work_pension_data['monthly_pension_amount'] = int(float(monthly_pension) * 100)
            work_pension = WorkPension.objects.create(**has_work_pension_data)
            basic_info.has_work_pension = work_pension
            basic_info.save()
        
        for account_data in investment_accounts_data:
            balance = account_data.get('balance')
            if balance is not None:
                account_data['balance'] = int(float(balance) * 100)
            
            monthly_contribution = account_data.get('monthly_contribution')
            if monthly_contribution is not None:
                account_data['monthly_contribution'] = int(float(monthly_contribution) * 100)
            
            InvestmentAccount.objects.create(basic_information=basic_info, **account_data)
        
        current_age = validated_data.get('current_age')
        for event_data in life_events_data:
            amount = event_data.get('amount')
            if amount is not None:
                event_data['amount'] = int(float(amount) * 100)
            
            LifeEvent.objects.create(basic_information=basic_info, **event_data)
        
        return basic_info

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        if instance.yearly_income_for_ideal_lifestyle is not None:
            representation['yearly_income_for_ideal_lifestyle'] = float(instance.yearly_income_for_ideal_lifestyle) / 100
        
        if instance.cpp_amount_at_age is not None:
            representation['cpp_amount_at_age'] = float(instance.cpp_amount_at_age) / 100
        
        if instance.oas_amount_at_OAS_age is not None:
            representation['oas_amount_at_OAS_age'] = float(instance.oas_amount_at_OAS_age) / 100
        
        if instance.has_work_pension and instance.has_work_pension.monthly_pension_amount is not None:
            representation['has_work_pension']['monthly_pension_amount'] = float(instance.has_work_pension.monthly_pension_amount) / 100
        
        investment_accounts = instance.investment_accounts.all()
        if investment_accounts:
            accounts_list = []
            for account in investment_accounts:
                account_data = {
                    'account_type': account.account_type,
                    'balance': float(account.balance) / 100 if account.balance is not None else None,
                    'monthly_contribution': float(account.monthly_contribution) / 100 if account.monthly_contribution is not None else None,
                    'investment_profile': account.investment_profile
                }
                accounts_list.append(account_data)
            representation['investment_accounts'] = accounts_list
        else:
            representation['investment_accounts'] = []
        
        life_events = instance.life_events.all()
        if life_events:
            events_list = []
            for event in life_events:
                event_data = {
                    'name': event.name,
                    'event_type': event.event_type,
                    'frequency': event.frequency,
                    'amount': float(event.amount) / 100 if event.amount is not None else 0,
                    'start_age': event.start_age,
                    'end_age': event.end_age,
                    'account': event.account,
                    'notes': event.notes
                }
                events_list.append(event_data)
            representation['life_events'] = events_list
        else:
            representation['life_events'] = []
        
        return representation

