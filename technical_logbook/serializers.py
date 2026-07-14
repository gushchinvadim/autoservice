from rest_framework import serializers
from decimal import Decimal
from .models import (
    Car, MaintenanceTask, MaintenanceRecord, MaintenanceRecordTask,
    SparePart, UsedPart, TaskRequiredPart, MaintenancePackage, CarModel
)


class SparePartSerializer(serializers.ModelSerializer):
    unit_display = serializers.CharField(source='get_unit_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = SparePart
        fields = [
            'id', 'name', 'manufacturer', 'category', 'category_display',
            'unit', 'unit_display', 'expected_lifespan_km', 'expected_lifespan_months',
            'current_price'
        ]


class TaskRequiredPartSerializer(serializers.ModelSerializer):
    """Сериализатор для нормативов расхода (связь задачи с запчастями)"""
    part_name = serializers.CharField(source='part.name', read_only=True)
    manufacturer = serializers.CharField(source='part.manufacturer', read_only=True)
    unit = serializers.CharField(source='part.get_unit_display', read_only=True)
    unit_price = serializers.DecimalField(source='part.current_price', max_digits=10, decimal_places=2, read_only=True)
    estimated_cost = serializers.SerializerMethodField()

    class Meta:
        model = TaskRequiredPart
        fields = [
            'id', 'task', 'part', 'part_name', 'manufacturer',
            'unit', 'quantity', 'unit_price', 'estimated_cost', 'car_model'
        ]

    def get_estimated_cost(self, obj):
        """Рассчитываем стоимость: цена запчасти × количество"""
        try:
            return float(obj.part.current_price * Decimal(str(obj.quantity)))
        except (TypeError, ValueError, AttributeError):
            return 0.0


class MaintenanceTaskSerializer(serializers.ModelSerializer):
    """Сериализатор для регламентных операций"""
    system_name = serializers.CharField(source='system.name', read_only=True)
    car_model_name = serializers.CharField(source='car_model.__str__', read_only=True, default=None)
    required_parts = TaskRequiredPartSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = MaintenanceTask
        fields = [
            'id', 'name', 'system', 'system_name', 'car_model', 'car_model_name',
            'interval_km', 'interval_months', 'labor_cost', 'required_parts'
        ]


class MaintenanceRecordTaskSerializer(serializers.ModelSerializer):
    """Сериализатор для выполненных операций в записи ТО"""
    task_name = serializers.CharField(source='task.name', read_only=True)
    system_name = serializers.CharField(source='task.system.name', read_only=True)
    labor_cost = serializers.DecimalField(source='task.labor_cost', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = MaintenanceRecordTask
        fields = ['id', 'task', 'task_name', 'system_name', 'labor_cost']


class UsedPartSerializer(serializers.ModelSerializer):
    """Сериализатор для установленных запчастей в записи ТО"""
    part_name = serializers.CharField(source='part.name', read_only=True)
    manufacturer = serializers.CharField(source='part.manufacturer', read_only=True)
    unit = serializers.CharField(source='part.get_unit_display', read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = UsedPart
        fields = [
            'id', 'part', 'part_name', 'manufacturer', 'unit',
            'quantity', 'unit_price', 'total_price', 'failed_prematurely'
        ]

    def get_total_price(self, obj):
        """Рассчитываем общую стоимость запчасти"""
        try:
            return float(Decimal(str(obj.unit_price)) * Decimal(str(obj.quantity)))
        except (TypeError, ValueError, AttributeError):
            return 0.0


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    # Поле для получения списка ID задач при создании/обновлении
    performed_tasks = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=MaintenanceTask.objects.all(),
        write_only=True,
        required=False
    )

    # Поле для вложенного создания запчастей
    used_parts = UsedPartSerializer(many=True, required=False)

    # Поля для отображения при GET-запросе
    tasks_display = serializers.SerializerMethodField()
    used_parts_display = UsedPartSerializer(source='used_parts', many=True, read_only=True)

    # ДОБАВЛЯЕМ ЭТО ПОЛЕ:
    package_name = serializers.CharField(source='package.name', read_only=True, default=None)

    class Meta:
        model = MaintenanceRecord
        fields = [
            'id', 'car', 'package', 'package_name', 'date_performed', 'mileage_at_service',
            'labor_cost', 'cost', 'notes',
            'performed_tasks', 'tasks_display',
            'used_parts', 'used_parts_display'
        ]
        read_only_fields = ['cost']


    def get_tasks_display(self, obj):
        """Возвращает список названий выполненных задач"""
        return [
            {
                'id': rt.task.id,
                'name': rt.task.name,
                'system': rt.task.system.name,
                'labor_cost': float(rt.task.labor_cost) if rt.task.labor_cost else 0
            }
            for rt in obj.performed_tasks.all()
        ]

    def create(self, validated_data):
        """Создание записи о ТО с вложенными задачами и запчастями"""
        performed_tasks_data = validated_data.pop('performed_tasks', [])
        used_parts_data = validated_data.pop('used_parts', [])

        # 1. Создаем саму запись о ТО
        record = MaintenanceRecord.objects.create(**validated_data)

        # 2. Создаем связи с выполненными задачами
        for task in performed_tasks_data:
            MaintenanceRecordTask.objects.create(record=record, task=task)

        # 3. Создаем записи об использованных запчастях
        for part_data in used_parts_data:
            UsedPart.objects.create(record=record, **part_data)

        # 4. Пересчитываем и сохраняем общую стоимость
        total_parts_cost = sum(
            Decimal(str(p.unit_price)) * Decimal(str(p.quantity))
            for p in record.used_parts.all()
        )
        record.cost = total_parts_cost + Decimal(str(record.labor_cost or 0))
        record.save(update_fields=['cost'])

        return record

    def update(self, instance, validated_data):
        """Обновление записи о ТО"""
        performed_tasks_data = validated_data.pop('performed_tasks', None)
        used_parts_data = validated_data.pop('used_parts', None)

        # Обновляем основные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Обновляем задачи (полная замена)
        if performed_tasks_data is not None:
            instance.performed_tasks.all().delete()
            for task in performed_tasks_data:
                MaintenanceRecordTask.objects.create(record=instance, task=task)

        # Обновляем запчасти (полная замена)
        if used_parts_data is not None:
            instance.used_parts.all().delete()
            for part_data in used_parts_data:
                UsedPart.objects.create(record=instance, **part_data)

        # Пересчитываем стоимость
        total_parts_cost = sum(
            Decimal(str(p.unit_price)) * Decimal(str(p.quantity))
            for p in instance.used_parts.all()
        )
        instance.cost = total_parts_cost + Decimal(str(instance.labor_cost or 0))
        instance.save(update_fields=['cost'])

        return instance


class CarSerializer(serializers.ModelSerializer):
    """Сериализатор для автомобилей"""
    car_model_name = serializers.CharField(source='car_model.__str__', read_only=True)
    last_maintenance = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = [
            'id', 'car_model', 'car_model_name', 'vin', 'license_plate',
            'current_mileage', 'first_registration_date', 'last_maintenance'
        ]

    def get_last_maintenance(self, obj):
        last_rec = obj.maintenance_records.first()
        if last_rec:
            return f"{last_rec.mileage_at_service} км ({last_rec.date_performed})"
        return "Нет истории"


class CarModelSerializer(serializers.ModelSerializer):
    """Сериализатор для моделей автомобилей"""

    class Meta:
        model = CarModel
        fields = ['id', 'make', 'model', 'engine', 'year_from', 'year_to']