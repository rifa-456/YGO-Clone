import os
from typing import Optional

from engine.core.resource_loader import ResourceLoader
from engine.logger import Logger
from engine.core.textures import Texture, ImageTextureFormatLoader


class TextureRegistry:
    """
    Autoload singleton for preloading all texture assets.
    """

    _initialized: bool = False
    FALLBACK_PATH: str = "assets/cards/back.png"

    @classmethod
    def initialize(cls) -> None:
        """
        Scans the assets directory and preloads all PNG files into the ResourceLoader cache.
        Call this once at engine startup, before any scenes are instantiated.
        """
        if cls._initialized:
            Logger.warn(
                "TextureRegistry already initialized. Skipping.", "TextureRegistry"
            )
            return

        Logger.info("Initializing Texture Registry...", "TextureRegistry")
        ResourceLoader.add_resource_format_loader(ImageTextureFormatLoader())
        assets_root = "assets"
        if not os.path.exists(assets_root):
            Logger.error(
                f"Assets directory not found: {assets_root}", "TextureRegistry"
            )
            return

        loaded_count = 0
        for root, dirs, files in os.walk(assets_root):
            for file in files:
                if file.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    rel_path = os.path.join(root, file)
                    rel_path = rel_path.replace("\\", "/")
                    texture = ResourceLoader.load(rel_path, Texture)
                    if texture:
                        loaded_count += 1
                        Logger.info(f"Preloaded texture: {rel_path}", "TextureRegistry")
                    else:
                        Logger.error(
                            f"Failed to preload texture: {rel_path}", "TextureRegistry"
                        )

        Logger.info(
            f"Texture Registry initialized. Loaded {loaded_count} textures.",
            "TextureRegistry",
        )
        cls._initialized = True

    @classmethod
    def get(cls, path: str) -> Optional[Texture]:
        """
        Retrieves a preloaded texture by its relative path.
        Includes graceful fallback if the asset is missing.

        Args:
            path: Relative path from project root (e.g., "assets/cards/back.png")

        Returns:
            Texture resource (Requested or Fallback), or None if critical failure.
        """
        path = path.replace("\\", "/")
        texture = ResourceLoader.load(path, Texture)
        if texture:
            return texture

        Logger.warn(
            f"MISSING ASSET: '{path}'. Using fallback placeholder.", "TextureRegistry"
        )
        fallback = ResourceLoader.load(cls.FALLBACK_PATH, Texture)
        if fallback:
            return fallback

        Logger.error("CRITICAL: Fallback texture also missing!", "TextureRegistry")
        return None
