# Tools at origin

Run a local mean calculation with a repeatability receipt (the digest detects changes but is not a signature): `python3 tools_origin.py mean --unit m 1 2 6`. This free calculation requires no account. Python 3.12 or newer and the versions in requirements.txt are required; cryptography is Apache-2.0 OR BSD-3-Clause. Run tests with `python3 -m unittest discover -v`.

The signed plan format is proposed. Plan verification accepts a local raw Ed25519 public-key path and independently authenticated SHA-256 pin, together with an injected secure store. No production public key or secure-store adapter is supplied. The only supported plan operation is the bounded mean calculation. Outbound approval is a refusing stub. The client does not launch external programs.

| Capability | Status |
| --- | --- |
| Mean calculation and local receipt | Available |
| Signed plan and device binding | Proposed, trust root pending |
| Outbound data | Unavailable |

The hash-locked installation file targets CPython 3.12 on x86-64 Linux with glibc 2.34 or newer: `python3 -m pip install --require-hashes --only-binary=:all: -r requirements.lock`. Other platforms need independently verified distribution hashes. CI runs the offline tests on the stated target; hosted CI has not yet run for this candidate.

Floating-point results may differ across Python versions or platforms; a repeatability receipt is not a cross-platform guarantee. The JSON stdin and byte-plan interfaces reject inputs over 65,536 bytes before parsing. The in-memory `run_plan` interface receives an already materialized object and cannot bound the caller’s prior allocation.
