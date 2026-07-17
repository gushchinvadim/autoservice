# technical_logbook/admin_views.py
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .forms import ImportPartsForm, ImportMaintenanceForm
from .models import SparePart, MaintenanceTask, CarSystem


@staff_member_required
def import_parts_view(request):
    """View для импорта запчастей из Excel"""

    # Словари для преобразования человекочитаемых значений в коды
    CATEGORY_MAP = {
        'масла и жидкости': 'oil',
        'масло': 'oil',
        'фильтры': 'filter',
        'электрика': 'electrical',
        'двигатель': 'engine',
        'трансмиссия': 'transmission',
        'подвеска': 'suspension',
        'прочее': 'other',
    }

    UNIT_MAP = {
        'штука': 'pcs',
        'шт': 'pcs',
        'литр': 'liters',
        'л': 'liters',
        'килограмм': 'kg',
        'кг': 'kg',
        'комплект': 'set',
        'компл': 'set',
    }

    if request.method == 'POST':
        form = ImportPartsForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']

            try:
                df = pd.read_excel(excel_file)
            except Exception as e:
                messages.error(request, f'Ошибка чтения файла: {e}')
                return redirect('import_parts')

            created = 0
            updated = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    # Пропускаем пустые строки
                    if pd.isna(row.get('name')):
                        continue

                    # Преобразуем категорию
                    category_raw = str(row.get('category', 'other')).strip().lower()
                    category = CATEGORY_MAP.get(category_raw, 'other')

                    # Преобразуем единицу измерения
                    unit_raw = str(row.get('unit', 'pcs')).strip().lower()
                    unit = UNIT_MAP.get(unit_raw, 'pcs')

                    # Обрабатываем числовые поля (могут быть пустыми)
                    expected_km = None
                    if pd.notna(row.get('expected_lifespan_km')):
                        try:
                            expected_km = int(float(row['expected_lifespan_km']))
                        except (ValueError, TypeError):
                            expected_km = None

                    expected_months = None
                    if pd.notna(row.get('expected_lifespan_months')):
                        try:
                            expected_months = int(float(row['expected_lifespan_months']))
                        except (ValueError, TypeError):
                            expected_months = None

                    price = 0
                    if pd.notna(row.get('current_price')):
                        try:
                            price = float(row['current_price'])
                        except (ValueError, TypeError):
                            price = 0

                    # Ищем существующую запчасть или создаём новую
                    part, created_flag = SparePart.objects.get_or_create(
                        name=row['name'],
                        manufacturer=row['manufacturer'],
                        defaults={
                            'category': category,
                            'expected_lifespan_km': expected_km,
                            'expected_lifespan_months': expected_months,
                            'unit': unit,
                            'current_price': price,
                        }
                    )

                    if created_flag:
                        created += 1
                        messages.success(request, f'✓ Создано: {part.name} ({part.manufacturer})')
                    else:
                        # Обновляем существующую запчасть
                        part.category = category
                        part.expected_lifespan_km = expected_km if expected_km is not None else part.expected_lifespan_km
                        part.expected_lifespan_months = expected_months if expected_months is not None else part.expected_lifespan_months
                        part.unit = unit
                        part.current_price = price
                        part.save()
                        updated += 1

                except Exception as e:
                    errors.append(f'Строка {index + 2}: {e}')

            # Формируем итоговое сообщение
            msg = f'✅ Импорт запчастей завершён! Создано: {created}, Обновлено: {updated}'
            if errors:
                msg += f'\n⚠️ Ошибок: {len(errors)}. Первые 5: {errors[:5]}'
                messages.warning(request, msg)
            else:
                messages.success(request, msg)

            return redirect('import_parts')
    else:
        form = ImportPartsForm()

    return render(request, 'admin/import_parts.html', {'form': form, 'title': 'Импорт запчастей'})


@staff_member_required
def import_maintenance_view(request):
    """View для импорта регламентов из Excel"""

    if request.method == 'POST':
        form = ImportMaintenanceForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']

            try:
                df = pd.read_excel(excel_file)
            except Exception as e:
                messages.error(request, f'Ошибка чтения файла: {e}')
                return redirect('import_maintenance')

            created = 0
            updated = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    # Пропускаем пустые строки
                    if pd.isna(row.get('name')):
                        continue

                    # Получаем или создаём систему
                    system_name = str(row.get('system', 'Прочее')).strip()
                    system, _ = CarSystem.objects.get_or_create(name=system_name)

                    # Обрабатываем числовые поля
                    interval_km = None
                    if pd.notna(row.get('interval_km')):
                        try:
                            interval_km = int(float(row['interval_km']))
                        except (ValueError, TypeError):
                            interval_km = None

                    interval_months = None
                    if pd.notna(row.get('interval_months')):
                        try:
                            interval_months = int(float(row['interval_months']))
                        except (ValueError, TypeError):
                            interval_months = None

                    labor_cost = 0
                    if pd.notna(row.get('labor_cost')):
                        try:
                            labor_cost = float(row['labor_cost'])
                        except (ValueError, TypeError):
                            labor_cost = 0

                    # Ищем существующую задачу
                    task, created_flag = MaintenanceTask.objects.get_or_create(
                        name=row['name'],
                        system=system,
                        defaults={
                            'interval_km': interval_km,
                            'interval_months': interval_months,
                            'labor_cost': labor_cost,
                        }
                    )

                    if created_flag:
                        created += 1
                        messages.success(request, f'✓ Создано: {task.name} ({system.name})')
                    else:
                        # Обновляем существующую задачу
                        task.interval_km = interval_km if interval_km is not None else task.interval_km
                        task.interval_months = interval_months if interval_months is not None else task.interval_months
                        task.labor_cost = labor_cost
                        task.save()
                        updated += 1

                except Exception as e:
                    errors.append(f'Строка {index + 2}: {e}')

            # Формируем итоговое сообщение
            msg = f'✅ Импорт регламентов завершён! Создано: {created}, Обновлено: {updated}'
            if errors:
                msg += f'\n⚠️ Ошибок: {len(errors)}. Первые 5: {errors[:5]}'
                messages.warning(request, msg)
            else:
                messages.success(request, msg)

            return redirect('import_maintenance')
    else:
        form = ImportMaintenanceForm()

    return render(request, 'admin/import_maintenance.html', {'form': form, 'title': 'Импорт регламентов'})


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .forms import BulkNormForm
from .models import CarModel, MaintenanceTask, SparePart, TaskRequiredPart


@staff_member_required
def bulk_add_norms_view(request):
    """View для массового добавления нормативов расхода"""

    if request.method == 'POST':
        car_model_id = request.POST.get('car_model')

        if not car_model_id:
            messages.error(request, 'Выберите модель автомобиля')
            return redirect('admin:bulk_add_norms')

        car_model = CarModel.objects.get(id=car_model_id)
        created = 0
        updated = 0
        errors = []

        # Получаем все задачи и запчасти из POST
        tasks = MaintenanceTask.objects.all()

        for task in tasks:
            # Проверяем, есть ли данные для этой задачи
            part_id = request.POST.get(f'task_{task.id}_part')
            quantity = request.POST.get(f'task_{task.id}_quantity')

            if part_id and quantity:
                try:
                    part = SparePart.objects.get(id=part_id)
                    qty = float(quantity)

                    norm, created_flag = TaskRequiredPart.objects.get_or_create(
                        task=task,
                        part=part,
                        car_model=car_model,
                        defaults={'quantity': qty}
                    )

                    if created_flag:
                        created += 1
                    else:
                        norm.quantity = qty
                        norm.save()
                        updated += 1

                except Exception as e:
                    errors.append(f'{task.name}: {e}')

        msg = f'✅ Нормативы добавлены! Создано: {created}, Обновлено: {updated}'
        if errors:
            msg += f'\n⚠️ Ошибок: {len(errors)}'
            messages.warning(request, msg)
        else:
            messages.success(request, msg)

        return redirect('bulk_add_norms')
    else:
        form = BulkNormForm()
        tasks = MaintenanceTask.objects.all()
        parts = SparePart.objects.all()

    return render(request, 'admin/bulk_add_norms.html', {
        'form': form,
        'tasks': tasks,
        'parts': parts,
        'title': 'Массовое добавление нормативов'
    })