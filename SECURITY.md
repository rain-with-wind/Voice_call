# Security Policy

## Supported Scope

Security-sensitive areas in this project include:

- public backend routes
- room registration and room lookup flows
- exposed deployment configuration
- network-facing audio server commands

## Reporting a Vulnerability

Please do not post detailed exploit steps in a public issue before maintainers have a chance to review them.

When reporting a vulnerability, include:

- affected component or file
- reproduction steps
- impact assessment
- suggested mitigation if you have one

## Response Expectations

Best effort will be made to:

- acknowledge the report
- reproduce the issue
- assess severity
- prepare a fix or mitigation

## Deployment Advice

- do not expose development servers directly to the public internet
- use `gunicorn` or another production WSGI server for the backend
- place a reverse proxy such as `nginx` in front of public deployments
- restrict firewall rules to only the ports you intend to expose
- treat any room-management token as sensitive data
