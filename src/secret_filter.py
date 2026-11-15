"""Best-effort sanitization for *review/diff* copies, NOT restorable backups."""
import re
from typing import Tuple

RULES = [
    re.compile(r'^(\s*(?:enable\s+(?:secret|password)(?:\s+\d+)?|username\s+\S+\s+(?:password|secret)(?:\s+\d+)?|snmp-server\s+community|tacacs-server\s+key|radius-server\s+key|key-string|password|secret|encrypted-password|authentication-key|pre-shared-key|private-key|community)\s+).+$', re.I),
    re.compile(r'^(\s*set\s+.*?\s+(?:encrypted-password|plain-text-password|authentication-key|pre-shared-key|secret|community|private-key|password)\s+).+$', re.I),
    re.compile(r'^(\s*(?:set\s+)?(?:.*\s)?(?:key|secret|password)\s+)("[^"]+"|\S+)(\s*)$', re.I),
]
BLOCK_MARKERS = ('-----BEGIN PRIVATE KEY-----', '-----BEGIN RSA PRIVATE KEY-----', '-----BEGIN OPENSSH PRIVATE KEY-----', '-----BEGIN EC PRIVATE KEY-----')
END_MARKERS = ('-----END PRIVATE KEY-----', '-----END RSA PRIVATE KEY-----', '-----END OPENSSH PRIVATE KEY-----', '-----END EC PRIVATE KEY-----')
# Warning patterns are not necessarily all credentials; review before publication.
SUSPICIOUS = re.compile(r'(?i)(password|secret|community|private.key|authentication.key|pre.shared.key|token|key.string|credential)')


def redact_config(raw: str) -> Tuple[str, int, int]:
    if not isinstance(raw, str):
        raise TypeError('Configuration must be text')
    output, count, warnings = [], 0, 0
    in_key = False
    for line in raw.splitlines():
        if line in ('[REDACTED PRIVATE KEY BLOCK]', '[REDACTED: REVIEW REQUIRED]'):
            output.append(line)
            continue
        if any(marker in line for marker in BLOCK_MARKERS):
            in_key = True
            output.append('[REDACTED PRIVATE KEY BLOCK]')
            count += 1
            continue
        if in_key:
            if any(marker in line for marker in END_MARKERS):
                in_key = False
            continue
        candidate = line
        for pattern in RULES:
            match = pattern.match(line)
            if match:
                candidate = match.group(1) + '<REDACTED>'
                count += 1
                break
        if candidate == line and SUSPICIOUS.search(line):
            # Fail closed for *published copies*: replace unclear sensitive lines.
            candidate = '[REDACTED: REVIEW REQUIRED]'
            count += 1
            warnings += 1
        output.append(candidate)
    return '\n'.join(output).rstrip() + '\n', count, warnings
