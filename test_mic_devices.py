"""
Diagnostic script — tests each available input device for 2 seconds
and reports which one actually picks up real audio (non-zero amplitude).

Run this, and when it says "Recording on device X", speak/make noise
for those 2 seconds. At the end it prints a summary of max amplitude
per device — the device with the highest value is your real mic.
"""

import sounddevice as sd
import numpy as np

DURATION = 2  # seconds per device test
SAMPLE_RATE = 16000

devices = sd.query_devices()

# Only test devices that have at least 1 input channel
input_devices = [
    (idx, d) for idx, d in enumerate(devices) if d["max_input_channels"] > 0
]

print(f"\nFound {len(input_devices)} input-capable devices. Testing each for {DURATION}s...\n")
print("Speak or make noise during EACH test to see which device picks it up.\n")

results = []

for idx, dev in input_devices:
    name = dev["name"]
    print(f"--- Testing device {idx}: {name} ---")
    try:
        audio = sd.rec(
            int(DURATION * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            device=idx,
        )
        sd.wait()
        max_val = float(np.max(np.abs(audio)))
        print(f"    -> max amplitude: {max_val:.6f}")
        results.append((idx, name, max_val))
    except Exception as e:
        print(f"    -> FAILED: {e}")
        results.append((idx, name, None))
    print()

print("=" * 60)
print("SUMMARY (sorted by amplitude, highest first)")
print("=" * 60)

valid_results = [r for r in results if r[2] is not None]
valid_results.sort(key=lambda r: r[2], reverse=True)

for idx, name, max_val in valid_results:
    marker = "  <-- LIKELY YOUR REAL MIC" if max_val > 0.01 else ""
    print(f"Device {idx:3d}  max={max_val:.6f}  {name}{marker}")

failed = [r for r in results if r[2] is None]
if failed:
    print("\nDevices that failed to open:")
    for idx, name, _ in failed:
        print(f"  Device {idx}: {name}")