from django.db import models
from decimal import Decimal
from datetime import date
import math

# --- СПРАВОЧНИКИ И ПЛАНЫ ---

class CarSystem(models.Model):
    name = models.CharField("Название системы", max_length=100, unique=True)

    class Meta:
        verbose_name = "Система автомобиля"
        verbose_name_plural = "Системы автомобиля"

    def __str__(self):
        return self.name


class CarModel(models.Model):
    """Конкретная модель авто (Toyota Camry 2.5, BMW X5 3.0d)"""
    make = models.CharField("Марка", max_length=100)
    model = models.CharField("Модель", max_length=100)
    engine = models.CharField("Двигатель", max_length=100, blank=True)
    year_from = models.PositiveIntegerField("Год выпуска от", null=True, blank=True)
    year_to = models.PositiveIntegerField("Год выпуска до", null=True, blank=True)

    class Meta:
        verbose_name = "Модель автомобиля"
        verbose_name_plural = "Модели автомобилей"
        unique_together = ('make', 'model', 'engine')

    def __str__(self):
        return f"{self.make} {self.model} {self.engine}"


class MaintenanceTask(models.Model):
    name = models.CharField("Название операции", max_length=200)
    system = models.ForeignKey(CarSystem, on_delete=models.PROTECT, related_name='tasks', verbose_name="Система")
    car_model = models.ForeignKey(
        CarModel, on_delete=models.CASCADE, related_name='maintenance_tasks',
        verbose_name="Для модели авто", null=True, blank=True
    )
    interval_km = models.PositiveIntegerField("Интервал пробега (км)", null=True, blank=True)
    interval_months = models.PositiveIntegerField("Интервал времени (мес)", null=True, blank=True)
    labor_cost = models.DecimalField("Базовая стоимость работы (руб)", max_digits=10, decimal_places=2, default=0,
                                     blank=True)

    class Meta:
        verbose_name = "Регламентная операция"
        verbose_name_plural = "Регламентные операции"

    def __str__(self):
        model_str = f" [{self.car_model}]" if self.car_model else " [Универсальный]"
        interval_str = f"{self.interval_km} км" if self.interval_km else "—"
        return f"{self.name}{model_str} ({interval_str})"

class MaintenancePackage(models.Model):
    name = models.CharField("Название пакета", max_length=100)
    description = models.TextField("Описание", blank=True)
    default_interval_km = models.PositiveIntegerField("Рекомендуемый пробег (км)", null=True, blank=True)

    class Meta:
        verbose_name = "Пакет ТО"
        verbose_name_plural = "Пакеты ТО"

    def __str__(self):
        return self.name


class PackageTask(models.Model):
    package = models.ForeignKey(MaintenancePackage, on_delete=models.CASCADE)
    task = models.ForeignKey(MaintenanceTask, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField("Количество", default=1)
    is_auto_generated = models.BooleanField("Авто-распределение", default=True)

    class Meta:
        verbose_name = "Задача в пакете"
        verbose_name_plural = "Задачи в пакете"
        unique_together = ('package', 'task')


class MaintenanceCycle(models.Model):
    name = models.CharField("Название цикла", max_length=100, default="Стандартный")
    car_model = models.ForeignKey(
        CarModel,
        on_delete=models.CASCADE,
        related_name='cycles',
        verbose_name="Для модели авто",
        null=True, blank=True
    )
    total_mileage = models.PositiveIntegerField("Длина цикла (км)", default=120000)
    step_mileage = models.PositiveIntegerField("Шаг между ТО (км)", default=15000)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Цикл ТО"
        verbose_name_plural = "Циклы ТО"

    def __str__(self):
        return f"{self.name} ({self.total_mileage} км, шаг {self.step_mileage} км)"

    @property
    def positions_count(self):
        """Сколько позиций в цикле (120000 / 15000 = 8)"""
        return self.total_mileage // self.step_mileage

    def get_cycle_position(self, mileage):
        """Возвращает позицию в цикле для любого пробега"""
        position_in_cycle = mileage % self.total_mileage
        if position_in_cycle == 0:
            position_in_cycle = self.total_mileage
        return position_in_cycle

    def get_to_number(self, mileage):
        """Возвращает номер ТО (1-8) для любого пробега"""
        position = self.get_cycle_position(mileage)
        return position // self.step_mileage

    def get_to_name(self, mileage):
        """
        Возвращает название ТО по пробегу (например, 'ТО-180' для 180000 км)
        """
        # Вычисляем абсолютный пробег ТО
        to_position = math.ceil(mileage / self.step_mileage) * self.step_mileage
        # Округляем до тысяч для красивого отображения
        to_thousands = to_position // 1000
        return f"ТО-{to_thousands}"


# --- ЗАПЧАСТИ И НОРМАТИВЫ ---

class SparePart(models.Model):
    CATEGORY_CHOICES = [
        ('oil', 'Масла и жидкости'),
        ('filter', 'Фильтры'),
        ('electrical', 'Электрика'),
        ('engine', 'Двигатель'),
        ('transmission', 'Трансмиссия'),
        ('suspension', 'Подвеска'),
        ('other', 'Прочее'),
    ]

    UNIT_CHOICES = [
        ('pcs', 'Штука'),
        ('liters', 'Литр'),
        ('kg', 'Килограмм'),
        ('set', 'Комплект'),
    ]

    name = models.CharField("Название", max_length=200)
    manufacturer = models.CharField("Производитель", max_length=100)
    category = models.CharField("Категория", max_length=20, choices=CATEGORY_CHOICES)
    expected_lifespan_km = models.PositiveIntegerField("Ожидаемый ресурс (км)", null=True, blank=True)
    expected_lifespan_months = models.PositiveIntegerField("Ожидаемый ресурс (мес)", null=True, blank=True)
    unit = models.CharField("Единица измерения", max_length=10, choices=UNIT_CHOICES, default='pcs')
    current_price = models.DecimalField("Цена за единицу (руб)", max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Запчасть"
        verbose_name_plural = "Запчасти"
        unique_together = ('name', 'manufacturer')

    def __str__(self):
        return f"{self.name} ({self.manufacturer})"


class TaskRequiredPart(models.Model):
    task = models.ForeignKey(MaintenanceTask, on_delete=models.CASCADE, related_name='required_parts', verbose_name="Задача")
    part = models.ForeignKey(SparePart, on_delete=models.PROTECT, related_name='used_in_tasks', verbose_name="Запчасть")
    car_model = models.ForeignKey(
        CarModel,
        on_delete=models.CASCADE,
        verbose_name="Модель авто",
        null=True, blank=True  # Если пусто - норматив универсальный для всех
    )
    quantity = models.FloatField("Количество", default=1)

    class Meta:
        verbose_name = "Норматив расхода"
        verbose_name_plural = "Нормативы расхода"
        unique_together = ('task', 'part', 'car_model')

    def __str__(self):
        model_str = f" [{self.car_model}]" if self.car_model else " [Универсальный]"
        return f"{self.task.name}: {self.quantity} {self.part.unit} {self.part.name}{model_str}"


# --- ФАКТ И ИСТОРИЯ ---

class Car(models.Model):
    car_model = models.ForeignKey(
        CarModel,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cars',
        verbose_name="Модель"
    )
    vin = models.CharField("VIN", max_length=17, unique=True)
    license_plate = models.CharField("Гос. номер", max_length=20, blank=True)
    current_mileage = models.PositiveIntegerField("Текущий пробег (км)", default=0)
    first_registration_date = models.DateField("Дата первой регистрации", null=True, blank=True)

    class Meta:
        verbose_name = "Автомобиль"
        verbose_name_plural = "Автомобили"

    def __str__(self):
        return f"{self.car_model or 'Неизвестно'} ({self.vin})"


class MaintenanceRecord(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='maintenance_records',
                            verbose_name="Автомобиль")
    package = models.ForeignKey(MaintenancePackage, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name="Пакет ТО")
    date_performed = models.DateField("Дата проведения", default=date.today)
    mileage_at_service = models.PositiveIntegerField("Пробег на момент ТО (км)")
    labor_cost = models.DecimalField("Стоимость работ (руб)", max_digits=10, decimal_places=2, default=0, blank=True)
    cost = models.DecimalField("Общая стоимость", max_digits=10, decimal_places=2, default=0)
    notes = models.TextField("Примечания", blank=True)

    class Meta:
        verbose_name = "Запись о ТО"
        verbose_name_plural = "Записи о ТО"
        ordering = ['-date_performed']

    def __str__(self):
        return f"ТО {self.car} на {self.mileage_at_service} км"


class MaintenanceRecordTask(models.Model):
    record = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name='performed_tasks', verbose_name="Запись ТО")
    task = models.ForeignKey(MaintenanceTask, on_delete=models.PROTECT, verbose_name="Операция")

    class Meta:
        verbose_name = "Выполненная операция"
        verbose_name_plural = "Выполненные операции"


class UsedPart(models.Model):
    record = models.ForeignKey(
        MaintenanceRecord, on_delete=models.CASCADE,
        related_name='used_parts', verbose_name="Запись ТО"
    )
    part = models.ForeignKey(
        SparePart, on_delete=models.PROTECT, verbose_name="Запчасть"
    )
    # Переименовали price → unit_price для ясности
    unit_price = models.DecimalField("Цена за единицу (руб)", max_digits=10, decimal_places=2,  blank=True )
    quantity = models.DecimalField("Количество", max_digits=10, decimal_places=2, default=1)
    failed_prematurely = models.BooleanField("Преждевременный выход из строя", default=False)

    class Meta:
        verbose_name = "Установленная запчасть"
        verbose_name_plural = "Установленные запчасти"

    @property
    def total_price(self):
        """Общая цена считается автоматически!"""
        return self.unit_price * self.quantity

    def save(self, *args, **kwargs):
        # АВТОПОДСТАНОВКА ЦЕНЫ: если цена не указана (или 0), берём из справочника
        if not self.unit_price or self.unit_price == 0:
            self.unit_price = self.part.current_price

        # --- Логика проверки качества (осталась без изменений) ---
        if not self.pk:
            prev = UsedPart.objects.filter(
                record__car=self.record.car, part=self.part
            ).exclude(record=self.record).order_by('-record__date_performed').first()

            if prev:
                days_used = (self.record.date_performed - prev.record.date_performed).days
                km_used = self.record.mileage_at_service - prev.record.mileage_at_service

                if self.part.expected_lifespan_months and days_used < (self.part.expected_lifespan_months * 30) * 0.3:
                    prev.failed_prematurely = True
                    prev.save(update_fields=['failed_prematurely'])
                if self.part.expected_lifespan_km and km_used < self.part.expected_lifespan_km * 0.3:
                    prev.failed_prematurely = True
                    prev.save(update_fields=['failed_prematurely'])

        super().save(*args, **kwargs)