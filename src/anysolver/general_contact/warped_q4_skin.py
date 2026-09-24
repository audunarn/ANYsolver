"""Physical reference skin geometry for the qualified varying-frame Q4.

This is a geometry/work-map prerequisite, not an admitted contact law. It
keeps the original bilinear Q4 and its formulation-owned physical director;
no search triangle is substituted for the surface.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


_Q4_MIXED_DERIVATIVE = np.array((0.25, -0.25, 0.25, -0.25))


@dataclass(frozen=True)
class WarpedQ4SkinSample:
    position: np.ndarray
    director: np.ndarray
    tangent_xi: np.ndarray
    tangent_eta: np.ndarray
    reference_measure: float


@dataclass(frozen=True)
class WarpedQ4GapCertificate:
    minimum_sampled_gap: float
    conservative_lower_gap: float
    cells_checked: int
    accuracy: float


class WarpedQ4Skin:
    """Evaluate one physical Q4 side using the accepted varying-frame route."""

    def __init__(self, model, element_id: int, side: str):
        from anysolver.e4_pl_element import QualifiedE4PLShellElement

        element = model.mesh.elements.get(element_id)
        if type(element) is not QualifiedE4PLShellElement:
            raise ValueError("warped skin needs a qualified Q4 element")
        if element.warped_formulation != "varying_frame":
            raise ValueError("warped skin needs the qualified varying-frame route")
        if side not in {"bottom", "midsurface", "top"}:
            raise ValueError("warped skin side must be bottom, midsurface or top")
        reference = np.asarray(element.get_node_coordinates(model.mesh), dtype=float)
        if reference.shape != (4, 3) or not np.all(np.isfinite(reference)):
            raise ValueError("warped skin needs four finite reference corners")
        self.element = element
        self.element_id = int(element_id)
        self.node_ids = tuple(int(node) for node in element.node_ids)
        self.reference = reference.copy()
        self.reference.setflags(write=False)
        self.side = side
        self.offset = {"bottom": -0.5, "midsurface": 0.0,
                       "top": 0.5}[side] * float(element.thickness)
        if not np.isfinite(self.offset):
            raise ValueError("warped skin offset is nonfinite")
        authority = element.physical_reference_director
        if authority is not None:
            alignments = []
            for xi in (-1.0, 1.0):
                for eta in (-1.0, 1.0):
                    _shape, derivative_xi, derivative_eta = (
                        element.compute_shape_functions(xi, eta)
                    )
                    cross = np.cross(derivative_xi @ self.reference,
                                     derivative_eta @ self.reference)
                    alignments.append(float(cross @ authority))
            if min(alignments) <= 0.0 <= max(alignments):
                raise ValueError("physical Q4 director polarity changes across the face")
        # Check the owner's frame and the physical offset surface at the
        # vertices, centre and interior before returning a usable adapter.
        for xi in (-1.0, 0.0, 1.0):
            for eta in (-1.0, 0.0, 1.0):
                self.sample(xi, eta)

    def sample(self, xi: float, eta: float) -> WarpedQ4SkinSample:
        xi, eta = float(xi), float(eta)
        if (not np.isfinite(xi) or not np.isfinite(eta)
                or abs(xi) > 1.0 or abs(eta) > 1.0):
            raise ValueError("Q4 skin parameters must be finite and inside [-1, 1]")
        shape, derivative_xi, derivative_eta = self.element.compute_shape_functions(
            xi, eta,
        )
        shape = np.asarray(shape, dtype=float)
        derivative_xi = np.asarray(derivative_xi, dtype=float)
        derivative_eta = np.asarray(derivative_eta, dtype=float)
        midsurface = shape @ self.reference
        tangent_xi = derivative_xi @ self.reference
        tangent_eta = derivative_eta @ self.reference
        numbered_frame, _dx, _dy, _mid_measure = (
            self.element._local_frame_and_derivatives(
                self.reference, derivative_xi, derivative_eta,
            )
        )
        physical_frame, _membrane, _curvature, _shear, _sign = (
            self.element._physical_director_context(numbered_frame)
        )
        director = np.asarray(physical_frame[:, 2], dtype=float)
        cross = np.cross(tangent_xi, tangent_eta)
        cross_norm = float(np.linalg.norm(cross))
        orientation = float(director @ cross / cross_norm)
        if abs(abs(orientation) - 1.0) > 1.0e-10:
            raise ValueError("physical Q4 director disagrees with varying-frame normal")
        mixed = _Q4_MIXED_DERIVATIVE @ self.reference
        projector = np.eye(3) - np.outer(director, director)
        director_xi = orientation * (projector @ np.cross(tangent_xi, mixed)) / cross_norm
        director_eta = orientation * (projector @ np.cross(mixed, tangent_eta)) / cross_norm
        skin_xi = tangent_xi + self.offset * director_xi
        skin_eta = tangent_eta + self.offset * director_eta
        skin_cross = np.cross(skin_xi, skin_eta)
        measure = float(np.linalg.norm(skin_cross))
        if (not np.isfinite(measure) or measure <= 0.0
                or float(skin_cross @ director) * orientation <= 0.0):
            raise ValueError("physical Q4 skin has an invalid or inverted measure")
        return WarpedQ4SkinSample(
            midsurface + self.offset * director,
            director.copy(), skin_xi, skin_eta, measure,
        )

    def conservative_bounds(self) -> tuple[np.ndarray, np.ndarray]:
        """Contain the whole reference skin, including non-nodal extrema."""

        reach = abs(self.offset)
        return (np.min(self.reference, axis=0) - reach,
                np.max(self.reference, axis=0) + reach)

    def certify_reference_plane_gap(
            self, plane_point: np.ndarray, plane_normal: np.ndarray, *,
            accuracy: float, maximum_cells: int, maximum_depth: int,
            ) -> WarpedQ4GapCertificate:
        """Bound the minimum physical reference-skin gap to an analytic plane.

        The Q4 midsurface projection is bilinear, so its minimum over a
        parametric rectangle occurs at a corner. Its unnormalized normal is
        affine in the two parameters. A lower bound on its norm therefore
        bounds variation of the unit physical director throughout each cell.
        """

        point = np.asarray(plane_point, dtype=float)
        normal = np.asarray(plane_normal, dtype=float)
        if (point.shape != (3,) or normal.shape != (3,)
                or not np.all(np.isfinite(point))
                or not np.all(np.isfinite(normal))
                or float(np.linalg.norm(normal)) <= 0.0):
            raise ValueError("warped Q4 plane needs a finite point and nonzero normal")
        normal = normal / np.linalg.norm(normal)
        if not np.isfinite(accuracy) or accuracy <= 0.0:
            raise ValueError("warped Q4 gap accuracy must be finite and positive")
        if (type(maximum_cells) is not int or maximum_cells < 1
                or type(maximum_depth) is not int or maximum_depth < 0):
            raise ValueError("warped Q4 gap budgets must be nonnegative integers")
        cached: dict[tuple[float, float], WarpedQ4SkinSample] = {}

        def at(xi: float, eta: float) -> WarpedQ4SkinSample:
            key = (xi, eta)
            if key not in cached:
                cached[key] = self.sample(xi, eta)
            return cached[key]

        point_dot = float(normal @ point)
        scale = max(float(np.max(np.abs(self.reference))),
                    float(np.max(np.abs(point))), abs(self.offset), 1.0)
        roundoff = 256.0 * np.finfo(float).eps * scale
        minimum_sampled = float("inf")
        minimum_lower = float("inf")
        cells_checked = 0
        cells = [(-1.0, 1.0, -1.0, 1.0, 0)]
        while cells:
            xi0, xi1, eta0, eta1, depth = cells.pop()
            cells_checked += 1
            if cells_checked > maximum_cells:
                raise MemoryError("warped Q4 gap cell budget exhausted")
            centre_xi, centre_eta = 0.5 * (xi0 + xi1), 0.5 * (eta0 + eta1)
            corners = tuple(at(xi, eta) for xi in (xi0, xi1)
                            for eta in (eta0, eta1))
            centre = at(centre_xi, centre_eta)
            sampled = min(float(normal @ sample.position) - point_dot
                          for sample in (*corners, centre))
            minimum_sampled = min(minimum_sampled, sampled)
            midsurface_min = min(
                float(normal @ (sample.position - self.offset * sample.director))
                for sample in corners
            )
            _shape, derivative_xi, derivative_eta = self.element.compute_shape_functions(
                centre_xi, centre_eta,
            )
            a = np.asarray(derivative_xi) @ self.reference
            b = np.asarray(derivative_eta) @ self.reference
            mixed = _Q4_MIXED_DERIVATIVE @ self.reference
            cross_norm = float(np.linalg.norm(np.cross(a, b)))
            variation = (
                0.5 * (xi1 - xi0) * float(np.linalg.norm(np.cross(a, mixed)))
                + 0.5 * (eta1 - eta0) * float(np.linalg.norm(np.cross(mixed, b)))
            )
            minimum_cross_norm = cross_norm - variation
            if minimum_cross_norm <= 0.0:
                lower = float("-inf")
            else:
                director_variation = variation / minimum_cross_norm
                lower = (midsurface_min + self.offset * float(normal @ centre.director)
                         - abs(self.offset) * director_variation - point_dot - roundoff)
            if lower >= minimum_sampled - accuracy:
                minimum_lower = min(minimum_lower, lower)
                continue
            if depth >= maximum_depth:
                raise MemoryError("warped Q4 gap depth budget exhausted")
            next_depth = depth + 1
            cells.extend((
                (xi0, centre_xi, eta0, centre_eta, next_depth),
                (centre_xi, xi1, eta0, centre_eta, next_depth),
                (xi0, centre_xi, centre_eta, eta1, next_depth),
                (centre_xi, xi1, centre_eta, eta1, next_depth),
            ))
        return WarpedQ4GapCertificate(
            float(minimum_sampled), float(minimum_lower), cells_checked,
            float(accuracy),
        )
