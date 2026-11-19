# core/management/commands/shrink_images.py
from io import BytesIO
from pathlib import Path

from django.apps import apps
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import models
from PIL import Image, ImageOps


class Command(BaseCommand):
    help = "Resize an ImageField and convert it to WebP. Example: shrink_images rooms.RoomImage image --max 1600"

    def add_arguments(self, parser):
        parser.add_argument("model", nargs="?")
        parser.add_argument("field", nargs="?")
        parser.add_argument("--max", type=int, default=1600)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--list", action="store_true", help="List every image/file field in the project")

    def handle(self, *args, **opts):
        if opts["list"] or not (opts["model"] and opts["field"]):
            for M in apps.get_models():
                for fld in M._meta.get_fields():
                    if isinstance(fld, models.FileField):
                        self.stdout.write(f"{M._meta.label} {fld.name}")
            return

        Model = apps.get_model(opts["model"])
        try:
            field = Model._meta.get_field(opts["field"])
        except Exception:
            self.stderr.write(f"{opts['model']} has no field '{opts['field']}'. Run with --list.")
            return
        if not isinstance(field, models.FileField):
            self.stderr.write(
                f"'{opts['field']}' on {opts['model']} is not an image field "
                f"(it's a {type(field).__name__}). Run with --list to find the right model."
            )
            return

        for obj in Model.objects.all():
            f = getattr(obj, opts["field"])
            if not f:
                continue
            try:
                img = ImageOps.exif_transpose(Image.open(f.path))
            except Exception as e:
                self.stderr.write(f"skip {obj.pk}: {e}")
                continue
            img.thumbnail((opts["max"], opts["max"]))
            buf = BytesIO()
            img.convert("RGB").save(buf, "WEBP", quality=80)
            before = Path(f.path).stat().st_size
            self.stdout.write(f"{obj.pk}: {before // 1024} KB -> {buf.tell() // 1024} KB")
            if opts["dry_run"]:
                continue
            old_path = f.path
            f.save(Path(f.name).stem + ".webp", ContentFile(buf.getvalue()), save=True)
            if old_path != f.path:
                Path(old_path).unlink(missing_ok=True)