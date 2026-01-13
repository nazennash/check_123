from rest_framework import serializers
from .models import BasicInformation, WorkPension, InvestmentAccount, LifeEvent


class WorkPensionSerializer(serializers.ModelSerializer):
    monthly_pension_amount = serializers.DecimalField(max_digits=20, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model = WorkPension
        fields = ['has_pension', 'monthly_pension_amount', 'pension_start_age']

    def validate_monthly_pension_amount(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Monthly pension amount cannot be negative.")
        return value

    def validate_pension_start_age(self, value):
        if value is not None and (value < 0 or value > 150):
            raise serializers.ValidationError("Pension start age must be between 0 and 150.")
        return value


class InvestmentAccountSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=20, decimal_places=2)
    monthly_contribution = serializers.DecimalField(max_digits=20, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model = InvestmentAccount
        fields = ['account_type', 'balance', 'monthly_contribution', 'investment_profile']

    def validate_balance(self, value):
        if value is None:
            raise serializers.ValidationError("balance is required.")
        if value < 0:
            raise serializers.ValidationError("Balance cannot be negative.")
        return value

    def validate_monthly_contribution(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Monthly contribution cannot be negative.")
        return value


class LifeEventSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        model = LifeEvent
        fields = ['name', 'event_type', 'frequency', 'amount', 'start_age', 'end_age', 'account', 'notes']

    def validate_frequency(self, value):
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

    def validate_start_age(self, value):
        if value < 0 or value > 150:
            raise serializers.ValidationError("start_age must be between 0 and 150.")
        return value

    def validate_end_age(self, value):
        if value < 0 or value > 150:
            raise serializers.ValidationError("end_age must be between 0 and 150.")
        return value

    def validate(self, data):
        start_age = data.get('start_age', 0)
        end_age = data.get('end_age', 0)
        if end_age < start_age:
            raise serializers.ValidationError("end_age cannot be less than start_age.")
        return data


class BasicInformationSerializer(serializers.ModelSerializer):
    has_work_pension = WorkPensionSerializer(required=False, allow_null=True)
    investment_accounts = InvestmentAccountSerializer(many=True, required=False)
    life_events = LifeEventSerializer(many=True, required=False)
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
            'investment_accounts',
            'life_events'
        ]
        read_only_fields = ['user_id']

    def validate_client_id(self, value):
        if value is None:
            raise serializers.ValidationError("client_id is required.")
        if value < 0:
            raise serializers.ValidationError("client_id cannot be negative.")
        return value

    def validate_current_age(self, value):
        if value is None:
            raise serializers.ValidationError("current_age is required.")
        if value < 0 or value > 150:
            raise serializers.ValidationError("current_age must be between 0 and 150.")
        return value

    def validate_work_optional_age(self, value):
        if value is not None and (value < 0 or value > 150):
            raise serializers.ValidationError("work_optional_age must be between 0 and 150.")
        return value

    def validate_yearly_income_for_ideal_lifestyle(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Yearly income cannot be negative.")
        return value

    def validate_inflation_rate(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Inflation rate must be between 0 and 100.")
        return value

    def validate_return_after_work_optional(self, value):
        if value is not None and (value < -100 or value > 100):
            raise serializers.ValidationError("Return after work optional must be between -100 and 100.")
        return value

    def validate_plan_until_age(self, value):
        if value is not None and (value < 0 or value > 150):
            raise serializers.ValidationError("plan_until_age must be between 0 and 150.")
        return value

    def validate_cpp_start_age(self, value):
        if value is not None and (value < 0 or value > 150):
            raise serializers.ValidationError("cpp_start_age must be between 0 and 150.")
        return value

    def validate_cpp_amount_at_age(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("CPP amount cannot be negative.")
        return value

    def validate_oas_start_age(self, value):
        if value is not None and (value < 0 or value > 150):
            raise serializers.ValidationError("oas_start_age must be between 0 and 150.")
        return value

    def validate_oas_amount_at_OAS_age(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("OAS amount cannot be negative.")
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
        
        if hasattr(instance, 'investment_accounts'):
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
        
        if hasattr(instance, 'life_events'):
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
        
        return representation

