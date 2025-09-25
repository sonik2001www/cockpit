from django.db import migrations

EXCL_ENTITY = """
CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE crm_entity
ADD CONSTRAINT entity_validity_excl
EXCLUDE USING gist (
  entity_uid WITH =,
  tstzrange(valid_from, COALESCE(valid_to, 'infinity')) WITH &&
);
"""

EXCL_ENTITY_DETAIL = """
ALTER TABLE crm_entitydetail
ADD CONSTRAINT entity_detail_validity_excl
EXCLUDE USING gist (
  entity_uid WITH =,
  detail_code WITH =,
  tstzrange(valid_from, COALESCE(valid_to, 'infinity')) WITH &&
);
"""

class Migration(migrations.Migration):
    dependencies = [("crm", "0001_initial")]

    operations = [
        migrations.RunSQL(EXCL_ENTITY, reverse_sql="""
            ALTER TABLE crm_entity DROP CONSTRAINT IF EXISTS entity_validity_excl;
        """),
        migrations.RunSQL(EXCL_ENTITY_DETAIL, reverse_sql="""
            ALTER TABLE crm_entitydetail DROP CONSTRAINT IF EXISTS entity_detail_validity_excl;
        """),
    ]
