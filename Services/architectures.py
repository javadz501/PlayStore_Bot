SUPPORTED_ARCHITECTURES = ("arm64", "armv7")

ARCHITECTURE_ABIS = {
    "arm64": "arm64-v8a",
    "armv7": "armeabi-v7a",
}

UNSUPPORTED_ARCHITECTURES = {
    "x86": "The pinned gplaydl 2.x and alltech-gplay backends do not expose an x86 device profile.",
    "x86_64": "The pinned gplaydl 2.x and alltech-gplay backends do not expose an x86_64 device profile.",
}


def architecture_plan(mode: str, single_arch: str) -> tuple[str, ...]:
    normalized_mode = (mode or "all").strip().lower()
    if normalized_mode == "all":
        return SUPPORTED_ARCHITECTURES
    if normalized_mode == "single":
        selected = (single_arch or "arm64").strip().lower()
        if selected not in SUPPORTED_ARCHITECTURES:
            raise ValueError(f"Unsupported architecture: {selected}")
        return (selected,)
    raise ValueError("PLAY_ARCH_MODE must be either 'all' or 'single'")
