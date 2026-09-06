"""
Image Asset Analyzer — Section 18 of Master Implementation Specification.

Performs technical profiling, quality grading, perceptual hash calculation,
semantic tagging, and layout recommendations for document images.
"""
from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image

from core.assets.models import ImageAsset, ImageLayoutType, ImageQualityGrade


# Domain taxonomy for corporate mining report imagery
IMAGE_TOPIC_KEYWORDS = {
    "mining": ["mine", "opencast", "underground", "quarry", "pit", "overburden", "coal", "excavation"],
    "machinery": ["dragline", "shovel", "dumper", "drill", "dozer", "hemm", "machinery", "equipment"],
    "sustainability": ["solar", "plantation", "green", "environment", "tree", "reclamation", "eco", "renewable"],
    "safety": ["safety", "rescue", "training", "fire", "drill", "ppe", "inspection", "audit"],
    "dispatch": ["fmc", "conveyor", "rail", "siding", "loading", "silo", "transport", "wagon"],
    "csr": ["csr", "school", "hospital", "village", "water", "community", "skill", "sports"],
    "governance": ["board", "director", "meeting", "mou", "signing", "annual", "officials", "award"],
}


class ImageAssetAnalyzer:
    """
    Deterministically analyzes an image file, extracting technical metrics,
    computing exact and perceptual hashes, and assessing quality.
    """

    @staticmethod
    def compute_sha256(file_path: str) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def compute_dhash(img: Image.Image) -> str:
        """
        Computes 64-bit Difference Hash (dHash) using pure PIL.
        Resizes to 9x8 grayscale, then compares adjacent pixels in each row.
        """
        try:
            gray = img.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
            pixels = list(gray.getdata())
            # 8 rows, each row has 9 columns -> 8 comparisons per row = 64 bits
            bits = []
            for row in range(8):
                row_start = row * 9
                for col in range(8):
                    left = pixels[row_start + col]
                    right = pixels[row_start + col + 1]
                    bits.append("1" if left > right else "0")
            bit_str = "".join(bits)
            # Convert 64 bits to 16-character hex string
            return f"{int(bit_str, 2):016x}"
        except Exception:
            return ""

    @staticmethod
    def hamming_distance(hex1: str, hex2: str) -> int:
        """Calculate bitwise Hamming distance between two 16-character hex hashes."""
        if not hex1 or not hex2 or len(hex1) != 16 or len(hex2) != 16:
            return 64
        val1 = int(hex1, 16)
        val2 = int(hex2, 16)
        xor_val = val1 ^ val2
        return bin(xor_val).count("1")

    @classmethod
    def analyze_image(
        cls,
        file_path: str,
        source_document_id: Optional[str] = None,
        page_number: Optional[int] = None,
        provenance_id: Optional[str] = None,
    ) -> ImageAsset:
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"Image not found: {file_path}")

        file_size = os.path.getsize(file_path)
        sha256 = cls.compute_sha256(file_path)

        with Image.open(file_path) as img:
            width, height = img.size
            img_format = (img.format or p.suffix.replace(".", "").upper())
            dpi_info = img.info.get("dpi")
            dpi = int(dpi_info[0]) if dpi_info and isinstance(dpi_info, (tuple, list)) else None
            dhash = cls.compute_dhash(img)

        aspect_ratio = round(width / max(height, 1), 3)

        # Assess Quality Grade
        if width < 150 or height < 150:
            quality = ImageQualityGrade.UNSUITABLE
        elif width < 450 or height < 450:
            quality = ImageQualityGrade.LOW_RES
        elif width >= 1400 and height >= 800:
            quality = ImageQualityGrade.EXCELLENT
        else:
            quality = ImageQualityGrade.ACCEPTABLE

        # Determine Recommended Layout
        if aspect_ratio >= 1.7 and width >= 1200:
            layout = ImageLayoutType.SINGLE_HERO
        elif aspect_ratio <= 0.8:
            layout = ImageLayoutType.TWO_COLUMN_TEXT_IMAGE
        else:
            layout = ImageLayoutType.WITH_CAPTION

        # Extract Semantic Tags from Filename & Path
        tags = cls._extract_tags(p.name + " " + str(p.parent))

        asset_id = f"img_{uuid.uuid4().hex[:10]}"

        return ImageAsset(
            asset_id=asset_id,
            filename=p.name,
            file_path=str(p.resolve()),
            format=img_format,
            width=width,
            height=height,
            aspect_ratio=aspect_ratio,
            file_size_bytes=file_size,
            sha256_hash=sha256,
            phash=dhash,
            dpi=dpi,
            quality_grade=quality,
            is_duplicate=False,
            duplicate_of=None,
            caption=p.stem.replace("_", " ").replace("-", " ").title(),
            tags=tags,
            recommended_layout=layout,
            provenance_id=provenance_id,
            source_document_id=source_document_id,
            page_number=page_number,
        )

    @classmethod
    def _extract_tags(cls, text: str) -> List[str]:
        text_lower = text.lower()
        matched = set()
        for category, keywords in IMAGE_TOPIC_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    matched.add(category)
                    break
        return sorted(list(matched))
