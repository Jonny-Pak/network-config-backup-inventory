"""Allowlist check. Call BEFORE opening a network connection."""
import ipaddress
import os


def validate_target(host: str) -> str:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError('Only numeric management IP addresses are supported') from exc
    nets = [s.strip() for s in os.getenv('BACKUP_ALLOWED_CIDRS', '').split(',') if s.strip()]
    if not nets:
        raise RuntimeError('Set BACKUP_ALLOWED_CIDRS (e.g. 192.168.56.0/24) before live connections')
    if not any(ip in ipaddress.ip_network(net, strict=False) for net in nets):
        raise PermissionError(f'IP {ip} is outside the management allowlist')
    return str(ip)


def netmiko_security_options() -> dict:
    """Strict SSH host-key verification; seed known_hosts after fingerprint verification."""
    options = {'ssh_strict': True, 'system_host_keys': True, 'allow_agent': False}
    known_hosts = os.getenv('BACKUP_KNOWN_HOSTS')
    if known_hosts:
        from pathlib import Path
        path = Path(known_hosts).expanduser()
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[1] / path
        if not path.is_file():
            raise FileNotFoundError('BACKUP_KNOWN_HOSTS does not exist')
        options.update(alt_host_keys=True, alt_key_file=str(path))
    return options
