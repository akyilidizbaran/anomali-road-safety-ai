# Data Policy

## Repository Rule

Raw video, evidence image, plate image, face image, cabin image and license-restricted dataset files must not be committed to this repository, even when it is private.

## Allowed in Git

* Dataset cards.
* License notes.
* Split definition examples without private filenames.
* Small template CSV files.
* Aggregated metrics that do not expose personal data.

## Not Allowed in Git

* Raw camera videos.
* Frame crops.
* Evidence screenshots.
* Plate crops.
* Face or cabin images.
* Downloaded dataset archives.

## Storage Assumption

Sensitive data is stored in local/private backend storage during testing. Public documentation may reference local IDs, but not expose private media.
