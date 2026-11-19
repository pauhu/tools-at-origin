# Proposed key binding

A signed plan binds key_ref and device_ref to the requesting secure store, with iat, exp and plan_id. The client accepts only a pinned, independently authenticated Ed25519 public key. A production public key and platform secure-store adapter have not been supplied, so plan execution refuses by default. The local calculation remains available without a key. Keys are not included in receipts or error messages.
