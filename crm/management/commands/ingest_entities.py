import csv
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from crm.models import Entity, EntityType
from django.db import transaction


class Command(BaseCommand):
    help = "Batch ingest entities from CSV and optionally refresh snapshot"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            required=True,
            help="Path to CSV file with entities",
        )
        parser.add_argument(
            "--refresh-snapshot",
            action="store_true",
            help="Refresh entity snapshot after ingest",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = options["file"]
        refresh_snapshot = options["refresh_snapshot"]

        try:
            with open(file_path, newline="") as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    entity_type_code = row.get("entity_type_code")
                    display_name = row.get("display_name")

                    if not entity_type_code or not display_name:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Skipping row with missing fields: {row}"
                            )
                        )
                        continue

                    try:
                        etype = EntityType.objects.get(code=entity_type_code)
                    except EntityType.DoesNotExist:
                        raise CommandError(f"EntityType {entity_type_code} not found")

                    Entity.objects.create(
                        entity_uid=row.get("entity_uid"),
                        entity_type=etype,
                        display_name=display_name,
                        valid_from=timezone.now(),
                        is_current=True,
                        hashdiff=row.get("hashdiff", ""),
                    )

            self.stdout.write(self.style.SUCCESS("Batch ingest complete"))

            if refresh_snapshot:
                from crm.models import EntitySnapshot

                EntitySnapshot.objects.all().delete()
                for e in Entity.objects.filter(is_current=True):
                    EntitySnapshot.objects.create(
                        entity_uid=e.entity_uid,
                        entity_type=e.entity_type,
                        display_name=e.display_name,
                        valid_from=e.valid_from,
                    )
                self.stdout.write(self.style.SUCCESS("Snapshot refreshed"))

        except FileNotFoundError:
            raise CommandError(f"File not found: {file_path}")
