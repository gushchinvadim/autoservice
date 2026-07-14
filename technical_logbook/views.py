
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from decimal import Decimal
import math
from collections import defaultdict

from .models import (
    Car, MaintenanceTask, MaintenanceRecord, MaintenanceRecordTask,
    SparePart, UsedPart, TaskRequiredPart, MaintenanceCycle, CarModel
)
from .serializers import (
    CarSerializer, MaintenanceTaskSerializer, MaintenanceRecordSerializer,
    SparePartSerializer, CarModelSerializer
)


# ДОБАВЛЯЕМ ЭТОТ КЛАСС:
class SparePartViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления справочником запчастей.
    """
    queryset = SparePart.objects.all()
    serializer_class = SparePartSerializer

class CarViewSet(viewsets.ModelViewSet):
    queryset = Car.objects.all()
    serializer_class = CarSerializer

    @action(detail=True, methods=['get'])
    def forecast(self, request, pk=None):
        """
        Прогноз следующего ТО с учётом цикличности (например, 120 000 км).
        Возвращает разделённые суммы: запчасти, работы, итого.
        """
        car = self.get_object()
        current_mileage = car.current_mileage

        # Ищем цикл: сначала для этой модели, потом универсальный
        cycle = MaintenanceCycle.objects.filter(
            car_model=car.car_model, is_active=True
        ).first() or MaintenanceCycle.objects.filter(
            car_model__isnull=True, is_active=True
        ).first()

        if not cycle:
            return Response(
                {'error': 'Не настроен цикл ТО для этой модели'},
                status=status.HTTP_400_BAD_REQUEST
            )

        step = cycle.step_mileage  # например, 15 000
        total_cycle = cycle.total_mileage  # например, 120 000

        # Ближайшая позиция ТО в будущем
        next_to_position = math.ceil((current_mileage + 1) / step) * step

        # Все регламенты для этой модели + универсальные
        tasks = MaintenanceTask.objects.filter(
            Q(car_model=car.car_model) | Q(car_model__isnull=True)
        )

        upcoming_tasks = []

        for task in tasks:
            if not task.interval_km:
                continue

            # Последнее выполнение этой задачи на этом авто
            last_done = MaintenanceRecordTask.objects.filter(
                record__car=car, task=task
            ).order_by('-record__mileage_at_service').first()

            last_mileage = last_done.record.mileage_at_service if last_done else 0

            # Следующий пробег замены
            next_exact_mileage = last_mileage + task.interval_km

            # Округляем до ближайшей позиции ТО
            next_to_mileage = math.ceil(next_exact_mileage / step) * step

            # Если задача попадает в ближайшее ТО
            if next_to_mileage <= next_to_position:
                upcoming_tasks.append({
                    'task': task,
                    'next_mileage': next_to_mileage,
                    'km_left': next_to_mileage - current_mileage,
                    'to_number': cycle.get_to_number(next_to_mileage)
                })

        if not upcoming_tasks:
            return Response({'message': 'В ближайшее время ТО не требуется'})

        # ===== ШАГ 1: Собираем корзину запчастей =====
        cart = defaultdict(lambda: {'quantity': 0, 'part': None})

        task_ids = [item['task'].id for item in upcoming_tasks]

        # Ищем нормативы СПЕЦИФИЧНЫЕ для этой модели авто
        specific_norms = TaskRequiredPart.objects.filter(
            task_id__in=task_ids,
            car_model=car.car_model
        ).select_related('part')

        # Ищем УНИВЕРСАЛЬНЫЕ нормативы (car_model = None)
        universal_norms = TaskRequiredPart.objects.filter(
            task_id__in=task_ids,
            car_model__isnull=True
        ).select_related('part')

        # Собираем ID задач, для которых уже нашли специфичный норматив
        tasks_with_specific_norms = set(specific_norms.values_list('task_id', flat=True))

        # Объединяем: специфичные + универсальные (только для тех задач, где нет специфичных)
        all_required_parts = list(specific_norms) + [
            norm for norm in universal_norms if norm.task_id not in tasks_with_specific_norms
        ]

        # Считаем количество
        for req in all_required_parts:
            cart[req.part.id]['part'] = req.part
            cart[req.part.id]['quantity'] += req.quantity

        # ===== ШАГ 2: Считаем стоимость РАБОТ =====
        total_labor_cost = Decimal('0.00')
        for item in upcoming_tasks:
            total_labor_cost += item['task'].labor_cost

        # ===== ШАГ 3: Считаем стоимость ЗАПЧАСТЕЙ =====
        total_parts_cost = Decimal('0.00')
        parts_list = []

        for item in cart.values():
            part = item['part']
            qty = Decimal(str(item['quantity']))
            cost = part.current_price * qty
            total_parts_cost += cost

            parts_list.append({
                'part_id': part.id,
                'name': f"{part.name} ({part.manufacturer})",
                'quantity': item['quantity'],
                'unit': part.get_unit_display(),
                'unit_price': float(part.current_price),
                'total_price': float(cost)
            })

        parts_list.sort(key=lambda x: x['total_price'], reverse=True)

        # ===== ШАГ 4: Возвращаем результат =====
        return Response({
            'car': str(car),
            'current_mileage': current_mileage,
            'cycle_length': total_cycle,
            'next_to_position_km': next_to_position,
            'next_to_name': cycle.get_to_name(next_to_position),  # Новое поле
            'next_to_number': cycle.get_to_number(next_to_position),
            'tasks': [
                {
                    'name': item['task'].name,
                    'system': item['task'].system.name,
                    'next_mileage': item['next_mileage'],
                    'km_left': item['km_left'],
                    'to_number': item['to_number'],
                    'to_name': cycle.get_to_name(item['next_mileage']),  # Новое поле
                    'labor_cost': float(item['task'].labor_cost)
                }
                for item in upcoming_tasks
            ],
            'shopping_list': parts_list,
            'total_parts_cost': float(total_parts_cost),
            'total_labor_cost': float(total_labor_cost),
            'total_forecast_cost': float(total_parts_cost + total_labor_cost)
        })
class MaintenanceTaskViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceTask.objects.all()
    serializer_class = MaintenanceTaskSerializer


from rest_framework import viewsets, permissions


class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]  # <-- Вернули защиту

    def get_queryset(self):
        queryset = MaintenanceRecord.objects.all().order_by('-date_performed')
        car_id = self.request.query_params.get('car')
        if car_id is not None:
            queryset = queryset.filter(car_id=car_id)
        return queryset

class CarModelViewSet(viewsets.ModelViewSet):
    queryset = CarModel.objects.all()
    serializer_class = CarModelSerializer