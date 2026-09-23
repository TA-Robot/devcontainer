# Verification history: evidence integrity and installed operation

Add `integrity` to history items: `verified`, `missing`, `corrupt`, or `incomplete`.
A completed record is verified only if its bounded regular report file is in the
expected managed location, its digest matches the durable record, its JSON is
valid, and its identity/status metadata agrees with that record. Incomplete records
must remain incomplete. Missing/corrupt reports must remain in the ordered history
with their original metadata, rather than disappearing or breaking the whole page.
For this interface, accept report payloads up to 8 MiB and classify larger files
as corrupt without reading past that bound. This is a study-local inspection
resource cap, owned by the primary; revise it only before a new comparison if
real report-size evidence shows it excludes required use cases.
Do not follow substituted symlinks, block on special files, read an arbitrary path
from corrupted metadata, or repair history as part of inspection.

`verified` means report integrity, not current source freshness or passing command
acceptance. A failed report can be intact. Existing strict validation must still
reject stale, failed, missing, corrupted, and incomplete latest evidence.

Confirm the actual previous phase's database and report history remain readable
without rewriting old rows or fabricating verification. Ship the feature in the
normal and frozen container images and verify the installed CLI without mounting
current runtime source into the image. Document the distinctions and failure cases.
Keep earlier defaults and contracts compatible. Do not add another scheduler,
provider backend, or destructive report retention operation.
