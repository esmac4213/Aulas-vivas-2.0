from django.db import migrations


LEGACY_USER_TABLES = (
    "auth_user",
    "auth_user_groups",
    "auth_user_user_permissions",
    "django_admin_log",
)


def ensure_custom_user_table(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        tables = set(connection.introspection.table_names(cursor))
        for table in LEGACY_USER_TABLES:
            if table in tables:
                cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                if cursor.fetchone()[0]:
                    raise RuntimeError(
                        f"Cannot migrate app_login while {table} contains legacy data."
                    )

    Usuario = apps.get_model("app_login", "Usuario")
    if Usuario._meta.db_table not in tables:
        schema_editor.create_model(Usuario)


class Migration(migrations.Migration):
    dependencies = [
        ("app_login", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            ensure_custom_user_table,
            migrations.RunPython.noop,
        ),
    ]
