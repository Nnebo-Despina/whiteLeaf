import shutil
import subprocess
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import models


class Command(BaseCommand):
    help = "Compress a video FileField to web-friendly MP4. Example: shrink_videos rooms.Room video"

    def add_arguments(self, parser):
        parser.add_argument("model")
        parser.add_argument("field")
        parser.add_argument("--height", type=int, default=720, help="Max height in px (default 720)")
        parser.add_argument("--crf", type=int, default=28, help="Quality: lower = bigger/better (default 28)")
        parser.add_argument("--keep-audio", action="store_true", help="Keep sound (default: removed)")
        parser.add_argument("--skip-under", type=float, default=5, help="Skip files smaller than this many MB")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        if not shutil.which("ffmpeg"):
            self.stderr.write("ffmpeg not found. Run: winget install Gyan.FFmpeg  (then reopen the terminal)")
            return

        Model = apps.get_model(opts["model"])
        field = Model._meta.get_field(opts["field"])
        if not isinstance(field, models.FileField):
            self.stderr.write(f"'{opts['field']}' is not a file field. Run: python manage.py shrink_images --list")
            return

        for obj in Model.objects.all():
            f = getattr(obj, opts["field"])
            if not f:
                continue
            src = Path(f.path)
            if not src.exists():
                self.stderr.write(f"skip {obj.pk}: file not found at {src}")
                continue
            size_mb = src.stat().st_size / 1024 / 1024
            if size_mb < opts["skip_under"] or src.stem.endswith("-web"):
                self.stdout.write(f"{obj.pk}: {size_mb:.1f} MB, already small, skipped")
                continue
            if opts["dry_run"]:
                self.stdout.write(f"{obj.pk}: {size_mb:.1f} MB would be compressed ({src.name})")
                continue

            out = src.with_name(src.stem + "-web.mp4")
            cmd = [
                "ffmpeg", "-y", "-i", str(src),
                "-vf", f"scale=-2:'min({opts['height']},ih)'",
                "-c:v", "libx264", "-crf", str(opts["crf"]), "-preset", "slow",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            ]
            cmd += ["-c:a", "aac", "-b:a", "96k"] if opts["keep_audio"] else ["-an"]
            cmd.append(str(out))

            self.stdout.write(f"{obj.pk}: compressing {src.name} ({size_mb:.1f} MB)...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0 or not out.exists():
                self.stderr.write(f"skip {obj.pk}: ffmpeg failed\n{result.stderr[-500:]}")
                out.unlink(missing_ok=True)
                continue

            new_mb = out.stat().st_size / 1024 / 1024
            if new_mb >= size_mb:
                self.stdout.write(f"{obj.pk}: result not smaller ({new_mb:.1f} MB), keeping original")
                out.unlink()
                continue

            setattr(obj, opts["field"], Path(f.name).with_name(out.name).as_posix())
            obj.save(update_fields=[opts["field"]])
            if src != out:
                src.unlink(missing_ok=True)
            self.stdout.write(f"{obj.pk}: {size_mb:.1f} MB -> {new_mb:.1f} MB")