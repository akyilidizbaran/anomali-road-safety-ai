# Security and Repository Policy

## Repository Rule

Do not commit credentials, API keys, raw videos, evidence images, license-restricted datasets, model weights or files containing identifiable plate/face/cabin data. This rule applies even when the repository is private.

## Sensitive Files

The following must stay outside the Git repository:

* `.env` and environment-specific config files.
* API keys and service account credentials.
* Android keystores and signing files.
* Raw road videos.
* Evidence screenshots and crops.
* Model checkpoints and exported binary model artifacts.
* Any file containing personal contact, identity or payment data.

## Test Data Rule

Test videos should only include scenarios with permission and controlled storage. Raw videos and evidence images should be stored in private local/backend storage, not in Git.

## Incident Response

If a secret or private media file is accidentally committed:

1. Stop pushing new commits.
2. Rotate the exposed secret if applicable.
3. Remove the file from Git history.
4. Document the incident in `governance/security`.
