import os
import shutil
from pathlib import Path

import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import Upload, Product, SalesRecord


REQUIRED_COLUMNS = {"product_name", "sale_date", "quantity_sold"}


async def save_upload_file(file: UploadFile, user_id: str) -> tuple[str, str]:
    """Simpan file CSV ke disk, return (filename, path)."""
    upload_dir = Path(settings.UPLOAD_DIR) / user_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    dest = upload_dir / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    size_mb = dest.stat().st_size / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        dest.unlink()
        raise HTTPException(400, f"File terlalu besar. Maksimal {settings.MAX_UPLOAD_SIZE_MB}MB")

    return file.filename, str(dest)


def validate_csv(file_path: str) -> pd.DataFrame:
    """Baca CSV, validasi kolom wajib, dan bersihkan data."""
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"File tidak dapat dibaca sebagai CSV: {e}")

    df.columns = df.columns.str.lower().str.strip().str.replace(" ", "_")

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Kolom wajib tidak ditemukan: {missing}")

    # Hapus duplikasi
    before = len(df)
    df = df.drop_duplicates()

    # Hapus baris dengan nilai kosong di kolom wajib
    df = df.dropna(subset=list(REQUIRED_COLUMNS))

    # Parse tanggal
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    df = df.dropna(subset=["sale_date"])
    df["sale_date"] = df["sale_date"].dt.date

    # Pastikan quantity positif
    df["quantity_sold"] = pd.to_numeric(df["quantity_sold"], errors="coerce")
    df = df[df["quantity_sold"] > 0]

    if "revenue" in df.columns:
        df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")

    if "category" not in df.columns:
        df["category"] = None
    if "region" not in df.columns:
        df["region"] = None

    return df


async def process_upload(upload_id: str, file_path: str):
    """Pipeline utama: validasi → ingest ke DB. Dipanggil sebagai background task."""
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        upload = await db.get(Upload, upload_id)
        if not upload:
            return

        try:
            upload.status = "processing"
            await db.commit()

            df = validate_csv(file_path)

            # Kelompokkan berdasarkan produk unik
            product_cols = ["product_name", "category", "region"]
            products_df = df[product_cols].drop_duplicates(subset=["product_name"])

            product_map: dict[str, str] = {}
            for _, row in products_df.iterrows():
                product = Product(
                    upload_id=upload_id,
                    product_name=row["product_name"],
                    category=row.get("category"),
                    region=row.get("region"),
                )
                db.add(product)
                await db.flush()
                product_map[row["product_name"]] = product.id

            # Ingest sales records
            records = []
            for _, row in df.iterrows():
                pid = product_map.get(row["product_name"])
                if not pid:
                    continue
                records.append(SalesRecord(
                    product_id=pid,
                    sale_date=row["sale_date"],
                    quantity_sold=int(row["quantity_sold"]),
                    revenue=float(row["revenue"]) if pd.notna(row.get("revenue")) else None,
                ))

            db.add_all(records)
            upload.status = "done"
            await db.commit()

        except Exception as e:
            await db.rollback()
            upload.status = "error"
            upload.error_message = str(e)
            await db.commit()

