from django import forms

from technical_logbook.models import CarModel


class ImportPartsForm(forms.Form):
    """Форма для импорта запчастей из Excel"""
    excel_file = forms.FileField(
        label='Excel файл с запчастями',
        help_text='Выберите файл .xlsx с колонками: name, manufacturer, category, expected_lifespan_km, expected_lifespan_months, unit, current_price'
    )

class ImportMaintenanceForm(forms.Form):
    """Форма для импорта регламентов из Excel"""
    excel_file = forms.FileField(
        label='Excel файл с регламентами',
        help_text='Выберите файл .xlsx с колонками: name, system, car_model, interval_km, interval_months'
    )

class BulkNormForm(forms.Form):
    """Форма для массового добавления нормативов расхода"""
    car_model = forms.ModelChoiceField(
        queryset=CarModel.objects.all(),
        label='Модель автомобиля',
        required=True,
        help_text='Выберите модель авто, для которой добавляете нормативы'
    )