#!/usr/bin/env python3
"""
Test script to verify pdf2epub package functionality
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


def test_package_import():
    """Test that the package can be imported and has all expected components."""
    print("Testing package import...")

    try:
        import pdf2epub

        print(f"✓ Package imported successfully, version: {pdf2epub.__version__}")

        # Test main functions are available
        expected_functions = [
            "convert_pdf",
            "convert_to_epub",
            "AIPostprocessor",
            "add_pdfs_to_queue",
            "get_default_output_dir",
            "get_default_input_dir",
        ]

        for func_name in expected_functions:
            if hasattr(pdf2epub, func_name):
                print(f"✓ Function {func_name} available")
            else:
                print(f"✗ Function {func_name} missing")
                return False

        # Test convenience functions
        if hasattr(pdf2epub, "convert_pdf_to_markdown"):
            print("✓ Convenience function convert_pdf_to_markdown available")
        else:
            print("✗ Convenience function convert_pdf_to_markdown missing")
            return False

        if hasattr(pdf2epub, "convert_markdown_to_epub"):
            print("✓ Convenience function convert_markdown_to_epub available")
        else:
            print("✗ Convenience function convert_markdown_to_epub missing")
            return False

        return True

    except Exception as e:
        print(f"✗ Package import failed: {e}")
        return False


def test_cli_interface():
    """Test CLI interface works."""
    print("\nTesting CLI interface...")

    try:
        import subprocess
        import sys

        # Test CLI help
        result = subprocess.run(
            [sys.executable, "-m", "pdf2epub.cli", "--help"],
            cwd=os.path.dirname(__file__),
            env={**os.environ, "PYTHONPATH": os.path.dirname(__file__)},
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0 and "Convert PDF files to EPUB" in result.stdout:
            print("✓ CLI help works")
            return True
        else:
            print(f"✗ CLI help failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"✗ CLI test failed: {e}")
        return False


def test_basic_functionality():
    """Test basic functionality without dependencies."""
    print("\nTesting basic functionality...")

    try:
        import pdf2epub
        from pathlib import Path
        import tempfile

        # Test utility functions
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Test get_default_output_dir
            input_path = tmppath / "test.pdf"
            output_dir = pdf2epub.get_default_output_dir(input_path)
            expected = tmppath / "test"

            if output_dir == expected:
                print("✓ get_default_output_dir works correctly")
            else:
                print(f"✗ get_default_output_dir failed: {output_dir} != {expected}")
                return False

            # Test get_default_input_dir
            import os

            os.chdir(tmppath)
            input_dir = pdf2epub.get_default_input_dir()
            expected_input = tmppath / "input"

            if input_dir == expected_input and input_dir.exists():
                print("✓ get_default_input_dir works correctly")
            else:
                print(f"✗ get_default_input_dir failed: {input_dir}")
                return False

            # Test AIPostprocessor instantiation
            processor = pdf2epub.AIPostprocessor(tmppath)
            if processor.work_dir == tmppath:
                print("✓ AIPostprocessor instantiation works")
            else:
                print("✗ AIPostprocessor instantiation failed")
                return False

        return True

    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("PDF2EPUB Package Test Suite")
    print("=" * 40)

    tests = [
        test_package_import,
        test_cli_interface,
        test_basic_functionality,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1

    print(f"\nTest Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! Package is ready for distribution.")
        return 0
    else:
        print("❌ Some tests failed. Please review and fix issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
