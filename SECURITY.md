# Security Policy

## Supported Versions

BeamMP Server Configurator is released from `main` through automated GitHub Releases and versioned GHCR images.

| Version | Supported |
| --- | --- |
| Latest GitHub Release | Yes |
| `ghcr.io/v5u2/beammp-server-configurator:latest` | Yes |
| Current `main` branch | Yes |
| Older commits/tags/releases | No |

Security fixes are made against the current `main` branch, then shipped through the automated release process. Older releases are not backported.

## Reporting a Vulnerability

If you believe you have found a security vulnerability:

1. Do not open a public GitHub issue.
2. Use GitHub's private vulnerability reporting for this repository if available.
3. If private reporting is not available in your environment, contact the repository maintainer directly and include:
   - a clear description of the issue
   - affected authentication or deployment mode
   - reproduction steps or proof of concept
   - impact assessment
   - any suggested remediation

Please avoid publishing exploit details until the issue has been reviewed and a fix is available.

## Response Process

The intended response process is:

1. Acknowledge the report.
2. Confirm impact and affected deployment modes.
3. Prepare and test a fix on `main`.
4. Publish the fix through the automated GitHub release workflow and update documentation if deployment changes are required.

Severity and response timing depend on exploitability, exposure, and whether the issue affects the authenticated admin surface, backup data, or Docker control path.

## Security Updates

Security updates are distributed through:

- GitHub Releases created by the automated release workflow
- versioned GHCR container images such as `ghcr.io/v5u2/beammp-server-configurator:<version>`
- the floating `ghcr.io/v5u2/beammp-server-configurator:latest` tag for the newest release

Operators should upgrade to the latest release or latest supported container image after a security fix is published.

## Security Model

BeamMP Server Configurator is an administrative application for BeamMP server management with:

- an authenticated admin interface
- local configuration, server, and backup file access
- limited Docker control through a socket proxy
- optional SAML and OAuth2/OIDC single sign-on

The main trust boundaries are:

- admin authentication and session handling
- reverse proxy and TLS behavior in front of the app
- Docker socket proxy permissions and reachable endpoints
- local bind-mounted config, backup, and server data
- SSO identity provider metadata and callback configuration

## Deployment Expectations

Operators are expected to:

- run the latest supported version
- prefer versioned release images or the latest published release over older pinned commits
- terminate TLS at a trusted reverse proxy or load balancer in production
- keep `.env` secrets out of version control
- restrict access to bind-mounted config, backup, and server directories
- limit Docker socket exposure to the provided proxy pattern only

### Authentication Modes

`AUTH_MODE=NO_AUTH` should only be used in trusted local or otherwise isolated environments. Internet-exposed deployments should use `BASIC`, `SAML`, or `OAUTH`.

For `AUTH_MODE=BASIC`, use a strong `ADMIN_PASSWORD` and avoid shared credentials across environments.

For `AUTH_MODE=SAML` or `AUTH_MODE=OAUTH`, protect client secrets and certificates, verify callback URLs carefully, and ensure identity provider configuration matches the deployed host exactly.

### Docker Proxy

This project is designed to work through a restricted Docker socket proxy. Do not expose the raw Docker socket directly to the application container or to untrusted users.

### Persistent Data

The mounted config, backup, server, and BeamNG-MP data directories should be treated as sensitive operational data. Restrict filesystem and container access to trusted operators only.

## Built-In Security Controls

The current application includes:

- session-based admin authentication for local login mode
- SAML and OAuth2/OIDC SSO support
- authenticated access checks for sensitive endpoints outside `NO_AUTH`
- Docker access constrained through a purpose-built proxy configuration
- backup management separated from direct Docker control
- environment-based container targeting instead of user-supplied container names

## Operator Hardening Checklist

Recommended production checklist:

- set a strong `SECRET_KEY`
- use a strong `ADMIN_PASSWORD` if using `AUTH_MODE=BASIC`
- prefer SSO over shared local credentials where possible
- keep `AUTH_MODE=NO_AUTH` disabled for public deployments
- terminate TLS at a trusted reverse proxy
- keep Docker images and base OS packages current
- monitor logs for failed logins and unexpected restart activity
- review socket proxy permissions before broadening any Docker API access

## Scope Notes

This policy covers the BeamMP Server Configurator application and its documented deployment modes. It does not cover:

- vulnerabilities in third-party identity providers or reverse proxies
- misconfiguration of external infrastructure outside the app
- risks caused by intentionally exposing the app without authentication
- vulnerabilities in BeamMP itself or other separately deployed services

## Disclosure Guidance

Please coordinate disclosure with the maintainer. Public write-ups, advisories, or proof-of-concept releases should wait until users have had a reasonable opportunity to update.
