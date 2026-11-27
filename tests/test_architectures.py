import unittest

from Services.architectures import (
    ARCHITECTURE_ABIS,
    SUPPORTED_ARCHITECTURES,
    UNSUPPORTED_ARCHITECTURES,
    architecture_plan,
)


class ArchitecturePlanTests(unittest.TestCase):
    def test_all_mode_returns_all_four_abi_architectures(self):
        self.assertEqual(
            architecture_plan("all", "arm64"),
            ("arm64", "armv7", "x86_64", "x86"),
        )

    def test_single_mode_preserves_selected_architecture(self):
        self.assertEqual(architecture_plan("single", "armv7"), ("armv7",))

    def test_all_four_architectures_are_supported(self):
        self.assertEqual(UNSUPPORTED_ARCHITECTURES, {})
        self.assertEqual(
            set(SUPPORTED_ARCHITECTURES),
            {"arm64", "armv7", "x86_64", "x86"},
        )

    def test_abi_mapping(self):
        self.assertEqual(
            ARCHITECTURE_ABIS,
            {
                "arm64": "arm64-v8a",
                "armv7": "armeabi-v7a",
                "x86_64": "x86_64",
                "x86": "x86",
            },
        )

    def test_single_mode_accepts_each_supported_architecture(self):
        for arch in SUPPORTED_ARCHITECTURES:
            with self.subTest(arch=arch):
                self.assertEqual(architecture_plan("single", arch), (arch,))

    def test_unknown_architecture_is_rejected(self):
        with self.assertRaises(ValueError):
            architecture_plan("single", "mips")


if __name__ == "__main__":
    unittest.main()
