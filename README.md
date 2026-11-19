# Tools at origin

Run a local mean calculation with a repeatability receipt: `python3 tools_origin.py mean --unit m 1 2 6`. This free calculation requires no account. Python 3.9 or newer and cryptography 50.0.2 are required; cryptography is Apache-2.0 OR BSD-3-Clause. Run tests with `python3 -m unittest discover -v`.

The signed plan format is proposed. Plan verification accepts a local raw Ed25519 public-key path and independently authenticated SHA-256 pin, together with an injected secure store. No production public key or secure-store adapter is supplied. The only supported plan operation is the bounded mean calculation. Outbound approval is a refusing stub. The client does not launch external programs.

| Capability | Status |
| --- | --- |
| Mean calculation and local receipt | Available |
| Signed plan and device binding | Proposed, trust root pending |
| Outbound data | Unavailable |
