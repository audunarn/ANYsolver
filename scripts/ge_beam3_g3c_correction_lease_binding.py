"""One-shot correction compatibility binding; no mechanics or public API."""
from hashlib import sha256
import json

_CAPTURE = None


def _reject_constant(value):
    raise ValueError('nonfinite correction lease value: '+value)


def _object(pairs):
    made = {}
    for key, value in pairs:
        if key in made:
            raise ValueError('duplicate correction lease key: '+key)
        made[key] = value
    return made


def _strict(raw):
    if type(raw) is not bytes:
        raise ValueError('canonical correction lease bytes required')
    try:
        value = json.loads(raw.decode('ascii'), parse_constant=_reject_constant,
                           object_pairs_hook=_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('canonical correction lease required') from error
    canonical = (json.dumps(value, sort_keys=True, separators=(',', ':'),
                            allow_nan=False)+'\n').encode('ascii')
    if canonical != raw:
        raise ValueError('noncanonical correction lease')
    return value


def capture(lease_bytes):
    """Capture only after the reviewed worker has fully validated these bytes."""
    global _CAPTURE
    if _CAPTURE is not None:
        raise ValueError('correction lease already captured')
    lease = _strict(lease_bytes)
    compatibility = lease.get('runtime_compatibility')
    if (lease.get('kind') != 'G3C_PHYSICAL_PRIVATE_DEVELOPMENT'
            or type(compatibility) is not dict):
        raise ValueError('correction compatibility lease required')
    _CAPTURE = (sha256(lease_bytes).hexdigest(),
                sha256((json.dumps(compatibility, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False)+'\n').encode('ascii')).hexdigest())


def compatibility_identity():
    if _CAPTURE is None:
        raise ValueError('captured correction lease required')
    return _CAPTURE[1]


def lease_identity():
    if _CAPTURE is None:
        raise ValueError('captured correction lease required')
    return _CAPTURE[0]
