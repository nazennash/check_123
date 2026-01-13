from django.contrib import admin
from .models import Projection


@admin.register(Projection)
class ProjectionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'basic_information',
        'retirement_age',
        'projected_savings',
        'savings_needed',
        'extra_savings',
        'is_on_track',
        'success_probability',
        'run_out_age',
        'created_at'
    ]
    list_filter = ['is_on_track', 'created_at', 'retirement_age']
    search_fields = ['basic_information__client_id', 'basic_information__user_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('basic_information', 'retirement_age', 'created_at', 'updated_at')
        }),
        ('Savings Analysis', {
            'fields': ('projected_savings', 'savings_needed', 'extra_savings', 'is_on_track')
        }),
        ('Monte Carlo Results', {
            'fields': (
                'success_probability',
                'percentile_10',
                'percentile_25',
                'percentile_50',
                'percentile_75',
                'percentile_90'
            )
        }),
        ('Additional Data', {
            'fields': ('run_out_age', 'yearly_breakdown', 'monte_carlo_data'),
            'classes': ('collapse',)
        }),
    )
