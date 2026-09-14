"""Independent G4a response reconstruction; imports no transaction owner."""
from dataclasses import asdict, is_dataclass

import numpy as np

from anysolver._ge_beam3_fibre_section import PhysicalFibreSection
from anysolver._ge_beam3_g1_elastic import ElasticSection
from anysolver._ge_beam3_generalized_ellipsoid_section import (
    EllipsoidalGeneralizedSection,
)


def _plain(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def evaluate(definitions, strains, origins):
    if (type(definitions) is not tuple or type(strains) is not tuple
            or type(origins) is not tuple or len(definitions) != 3
            or len(strains) != 3 or len(origins) != 3):
        raise ValueError("exact independent G4a inventory required")
    rows = []
    for definition, strain, origin in zip(definitions, strains, origins):
        law = definition.law
        if type(law) is ElasticSection:
            response = law.response(strain, origin)
            rows.append(dict(station_id=definition.station_id,
                             law_identity=law.identity,
                             origin=[], history=[], strain=_plain(strain),
                             resultants=_plain(response["resultants"]),
                             tangent=_plain(response["tangent"]),
                             incremental_potential=[response["potential"], 0.0],
                             fibres=[]))
        elif type(law) is EllipsoidalGeneralizedSection:
            response = law.response(strain, origin=origin)
            rows.append(dict(station_id=definition.station_id,
                             law_identity=response.section_identity,
                             origin=_plain(response.origin),
                             history=_plain(response.history),
                             strain=_plain(strain),
                             resultants=_plain(response.resultants),
                             tangent=_plain(response.tangent),
                             incremental_potential=_plain(response.incremental_potential),
                             fibres=[]))
        elif type(law) is PhysicalFibreSection:
            response = law.response(strain, origin=origin)
            rows.append(dict(station_id=definition.station_id,
                             law_identity=response.section_identity,
                             origin=_plain(response.origin),
                             history=_plain(response.history),
                             strain=_plain(strain),
                             resultants=_plain(response.resultants),
                             tangent=_plain(response.tangent),
                             incremental_potential=_plain(response.incremental_potential),
                             fibres=_plain(response.fibres)))
        else:
            raise ValueError("foreign G4a law")
    return rows
