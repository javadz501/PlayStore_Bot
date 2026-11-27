SUPPORTED_ARCHITECTURES = ("arm64", "armv7", "x86_64", "x86")

ARCHITECTURE_ABIS = {
    "arm64": "arm64-v8a",
    "armv7": "armeabi-v7a",
    "x86_64": "x86_64",
    "x86": "x86",
}

UNSUPPORTED_ARCHITECTURES: dict[str, str] = {}


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
