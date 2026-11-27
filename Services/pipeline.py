import asyncio
import hashlib
import json
import logging
import zipfile
from pathlib import Path

from aiogram.types import Message

from Services.architectures import ARCHITECTURE_ABIS, UNSUPPORTED_ARCHITECTURES, architecture_plan
from Services.downloader import DownloadError
from Services.search import fetch_app_title
from Utils.filename import sanitize_filename_stem
from Utils.html import bold, safe
from Utils.keyboards import delivery_keyboard, main_keyboard
from Utils.progress import DiskSizeProgress
from Utils.texts import (
    CONVERTING_TEXT,
    DELIVERY_PROMPT_TEXT,
    DOWNLOAD_TITLE,
    FAILED_TEXT,
)

logger = logging.getLogger(__name__)


def _create_multi_arch_bundle(archive_path, package_name, successful_apks, failed_architectures):
    available = []
    for arch, apk_path in successful_apks.items():
        with apk_path.open("rb") as apk_file:
            digest = hashlib.file_digest(apk_file, "sha256").hexdigest()
        available.append({"architecture": arch, "abi": ARCHITECTURE_ABIS[arch], "file": apk_path.name, "sha256": digest})
    manifest = {
        "package_name": package_name,
        "mode": "all",
        "available_architectures": available,
        "unavailable_architectures": [
            {"architecture": arch, "status": "unsupported", "reason": reason}
            for arch, reason in UNSUPPORTED_ARCHITECTURES.items()
        ] + [
            {"architecture": arch, "status": "download_failed", "reason": reason}
            for arch, reason in failed_architectures.items()
        ],
        "universal": {
            "status": "not_generated",
            "reason": "Separate ARM APKs are not a Universal APK; configured backends do not return all ABI splits together.",
        },
    }
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for apk_path in successful_apks.values():
            bundle.write(apk_path, arcname=f"apks/{apk_path.name}")
        bundle.writestr("ARCHITECTURE_REPORT.json", json.dumps(manifest, indent=2, sort_keys=True))
    return archive_path


async def _rename_apk_for_app(apk_path: Path, package_name: str) -> Path:
    title = await fetch_app_title(package_name)
    stem = sanitize_filename_stem(title or package_name, fallback=package_name)
    target = apk_path.with_name(f"{stem}.apk")
    if target == apk_path:
        return apk_path
    try:
        if target.exists():
            target.unlink()
        apk_path.rename(target)
    except OSError as exc:
        logger.warning("rename %s -> %s failed: %s", apk_path, target, exc)
        return apk_path
    return target


async def run_download_pipeline(
    *,
    event_message: Message,
    user_id: int,
    url: str,
    package_name: str,
    deps: dict,
) -> None:
    db = deps["db"]
    downloader = deps["downloader"]
    converter = deps["converter"]
    settings = deps["settings"]

    job_id = await db.create_job(user_id, package_name, url)
    package_label = bold(package_name)

    mode = (getattr(settings, "play_arch_mode", "all") or "all").strip().lower()
    if mode not in {"all", "single"}:
        raise DownloadError("PLAY_ARCH_MODE must be either 'all' or 'single'")
    expected_suffix = ".zip" if mode == "all" else ".apk"
    cache = await db.get_package_cache(package_name)
    cached_apk = None
    if cache and cache.get("apk_path"):
        candidate = Path(cache["apk_path"])
        if candidate.exists() and candidate.suffix.lower() == expected_suffix:
            cached_apk = candidate

    if cached_apk is not None:
        if mode == "single":
            cached_apk = await _rename_apk_for_app(cached_apk, package_name)
        await db.set_package_apk(package_name, str(cached_apk))
        status_message = await event_message.answer(
            f"{DOWNLOAD_TITLE}\n\n{package_label}\n\n♻️ از کش استفاده شد"
        )
        await db.update_job(
            job_id, "ready", source_path=str(cached_apk), apk_path=str(cached_apk)
        )
        await status_message.edit_text(
            DELIVERY_PROMPT_TEXT, reply_markup=delivery_keyboard(job_id)
        )
        return

    status_message = await event_message.answer(
        f"{DOWNLOAD_TITLE}\n\n{package_label}\n\n📥 0 B  •  0 B/s"
    )

    download_dir = settings.download_dir / str(job_id)
    download_dir.mkdir(parents=True, exist_ok=True)
    download_progress: DiskSizeProgress | None = None

    try:
        download_progress = DiskSizeProgress(
            status_message, DOWNLOAD_TITLE, package_label, download_dir
        )
        download_progress.start()
        if mode == "all":
            if download_progress:
                await download_progress.stop()
                download_progress = None
            architectures = architecture_plan(mode, settings.play_arch)
            successful_apks = {}
            failed_architectures = {}
            app_title = await fetch_app_title(package_name)
            app_stem = sanitize_filename_stem(app_title or package_name, fallback=package_name)
            for arch in architectures:
                try:
                    await status_message.edit_text(f"{DOWNLOAD_TITLE}\n\n{package_label}\n\nDownloading {arch} ({ARCHITECTURE_ABIS[arch]})")
                    arch_progress = DiskSizeProgress(
                        status_message,
                        DOWNLOAD_TITLE,
                        package_label,
                        settings.download_dir / str(job_id) / arch,
                    )
                    arch_progress.start()
                    try:
                        source_path = await downloader.download_arch(
                            url=url, package_name=package_name, job_id=job_id, arch=arch
                        )
                    finally:
                        await arch_progress.stop()
                    await status_message.edit_text(f"{CONVERTING_TEXT}\n\n{arch}")
                    apk_path = await converter.to_apk(source_path)
                    variant_path = apk_path.with_name(f"{app_stem}-{arch}.apk")
                    if variant_path != apk_path:
                        if variant_path.exists():
                            variant_path.unlink()
                        apk_path.rename(variant_path)
                    successful_apks[arch] = variant_path
                except DownloadError as exc:
                    failed_architectures[arch] = str(exc)
                    logger.warning("Architecture download failed package=%s arch=%s: %s", package_name, arch, exc)
            if not successful_apks:
                details = "; ".join(f"{a}: {e}" for a, e in failed_architectures.items())
                raise DownloadError(f"هیچ نسخه معماری قابل تولید نبود. {details}")
            await status_message.edit_text("در حال ساخت بسته چندمعماری...")
            archive_path = settings.download_dir / str(job_id) / f"{app_stem}-multi-arch.zip"
            await asyncio.to_thread(_create_multi_arch_bundle, archive_path, package_name, successful_apks, failed_architectures)
            await db.update_job(job_id, "ready", source_path=str(settings.download_dir / str(job_id)), apk_path=str(archive_path))
            await db.set_package_apk(package_name, str(archive_path))
        else:
            source_path = await downloader.download(url=url, package_name=package_name, job_id=job_id)
            await db.update_job(job_id, "downloaded", source_path=str(source_path))
            await status_message.edit_text(CONVERTING_TEXT)
            apk_path = await converter.to_apk(source_path)
            apk_path = await _rename_apk_for_app(apk_path, package_name)
            await db.update_job(job_id, "ready", apk_path=str(apk_path))
            await db.set_package_apk(package_name, str(apk_path))
        if download_progress:
            await download_progress.stop()
            download_progress = None

        await status_message.edit_text(
            DELIVERY_PROMPT_TEXT, reply_markup=delivery_keyboard(job_id)
        )
    except DownloadError as exc:
        if download_progress:
            await download_progress.stop()
        await db.update_job(job_id, "failed", error=str(exc))
        await status_message.edit_text(
            FAILED_TEXT.format(error=safe(exc)),
            reply_markup=main_keyboard(),
        )
    except Exception as exc:
        if download_progress:
            await download_progress.stop()
        await db.update_job(job_id, "failed", error=str(exc))
        await status_message.edit_text(
            FAILED_TEXT.format(error=safe(exc)),
            reply_markup=main_keyboard(),
        )
