import pandas as pd
from django.core.management.base import BaseCommand
from django.db.models import Q
from technical_logbook.models import MaintenanceTask, CarSystem


class Command(BaseCommand):
    help = 'Импорт регламентных работ из Excel файла'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к Excel файлу')

    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            self.stderr.write(f'Ошибка чтения файла: {e}')
            return

        created = 0
        updated = 0

        for _, row in df.iterrows():
            # Пропускаем пустые строки
            if pd.isna(row['name']):
                continue

            # Получаем или создаём систему
            system_name = row['system']
            system, _ = CarSystem.objects.get_or_create(name=system_name)

            # Ищем существующую задачу
            task, created_flag = MaintenanceTask.objects.get_or_create(
                name=row['name'],
                system=system,
                defaults={
                    'interval_km': int(row['interval_km']) if pd.notna(row['interval_km']) else None,
                    'interval_months': int(row['interval_months']) if pd.notna(row['interval_months']) else None,
                }
            )

            if created_flag:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Создано: {task.name} ({system.name})'))
            else:
                updated += 1
                # Обновляем интервалы
                task.interval_km = int(row['interval_km']) if pd.notna(row['interval_km']) else task.interval_km
                task.interval_months = int(row['interval_months']) if pd.notna(
                    row['interval_months']) else task.interval_months
                task.save()
                self.stdout.write(self.style.WARNING(f'↻ Обновлено: {task.name} ({system.name})'))

        self.stdout.write(self.style.SUCCESS(f'\n✅ Готово! Создано: {created}, Обновлено: {updated}'))