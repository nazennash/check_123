from django.db import models
from api.models import BasicInformation


class Projection(models.Model):
    basic_information = models.ForeignKey(BasicInformation, on_delete=models.CASCADE, related_name='projections')
    retirement_age = models.IntegerField()
    projected_savings = models.DecimalField(max_digits=20, decimal_places=2)
    savings_needed = models.DecimalField(max_digits=20, decimal_places=2)
    extra_savings = models.DecimalField(max_digits=20, decimal_places=2)
    is_on_track = models.BooleanField(default=False)
    success_probability = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    percentile_10 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    percentile_25 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    percentile_50 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    percentile_75 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    percentile_90 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    run_out_age = models.IntegerField(null=True, blank=True)
    yearly_breakdown = models.JSONField(default=list)
    monte_carlo_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'projection'
        ordering = ['-created_at']
