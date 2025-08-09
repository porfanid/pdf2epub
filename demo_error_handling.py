#!/usr/bin/env python3
"""
Demo script showing how to use the enhanced error handling features
to troubleshoot the 'encoder' KeyError issue.
"""

import sys
from pathlib import Path

# Add the project to path
sys.path.insert(0, str(Path(__file__).parent))

from pdf2epub.pdf2md import print_troubleshooting_info, clear_model_cache


def demo_encoder_error_handling():
    """Demonstrate the enhanced error handling for encoder issues."""

    print("=== PDF2EPUB Enhanced Error Handling Demo ===\n")

    # Simulate the encoder error that users are experiencing
    print("1. Simulating the 'encoder' KeyError that users reported:")
    encoder_error = KeyError("'encoder'")
    print(f"   Original error: {encoder_error}")
    print("\n   Enhanced troubleshooting output:")
    print_troubleshooting_info(encoder_error)

    # Show other error types
    print("\n" + "=" * 50)
    print("2. Example of memory error handling:")
    memory_error = RuntimeError("CUDA out of memory")
    print_troubleshooting_info(memory_error)

    print("\n" + "=" * 50)
    print("3. Example of network error handling:")
    network_error = ConnectionError("Failed to connect to huggingface.co")
    print_troubleshooting_info(network_error)

    print("\n" + "=" * 50)
    print("4. Cache clearing utility demonstration:")
    print("   Users can now run: python3 main.py --clear-cache")
    print("   Or programmatically: clear_model_cache()")

    # Don't actually clear cache in demo
    print("   (Cache clearing not executed in demo mode)")

    print("\n" + "=" * 50)
    print("5. Key improvements for users:")
    print("   ✓ Specific error detection and categorization")
    print("   ✓ Step-by-step troubleshooting instructions")
    print("   ✓ Easy cache clearing with --clear-cache flag")
    print("   ✓ Comprehensive documentation in docs/TROUBLESHOOTING.md")
    print("   ✓ Better error messages in conversion pipeline")

    print(f"\nFor the original issue reported, users should:")
    print("1. Run: python3 main.py --clear-cache")
    print("2. Retry: python3 main.py 'Computer Vision Algorithms and Applications.pdf'")
    print("3. If still failing, check docs/TROUBLESHOOTING.md")


if __name__ == "__main__":
    demo_encoder_error_handling()
