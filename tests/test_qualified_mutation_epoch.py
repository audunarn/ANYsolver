from __future__ import annotations

import copy
import pickle

import pytest

from anysolver.fe_core import FEMesh


def test_qualified_direct_state_epoch_is_monotonic_fixed_and_copyable() -> None:
    mesh = FEMesh()
    token = mesh._qualified_direct_state_token
    assert isinstance(token, list)
    assert token == [0]

    mesh.add_node(1, 0.0, 0.0, 0.0)
    current = token[0]
    assert current > 0

    with pytest.raises(ValueError, match="only advance by one"):
        token[0] = current - 1
    with pytest.raises(ValueError, match="only advance by one"):
        token[0] = current + 2
    with pytest.raises(TypeError, match="fixed length"):
        token.append(current + 1)
    assert token == [current]

    token[0] = current + 1
    assert token == [current + 1]

    copied = copy.deepcopy(token)
    restored = pickle.loads(pickle.dumps(token))
    assert copied == token and copied is not token
    assert restored == token and restored is not token
    copied[0] = copied[0] + 1
    restored[0] = restored[0] + 1
