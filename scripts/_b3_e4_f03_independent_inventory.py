"""Proposed F03 classical-refinement inventory; no execution authority.

Cases are defined here so a future reviewed registration can bind exact
identities and reject duplicate or missing axes before any expensive run.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Mesh:
    n_s: int
    n_y: int
    n_beam: int
    n_mortar: int


@dataclass(frozen=True, order=True)
class Case:
    mesh: Mesh
    topology: str
    loading: str
    law: str

    @property
    def identity(self) -> str:
        m=self.mesh
        return (f'{self.topology}-{self.loading}-{self.law}-'
                f'Ns{m.n_s}-Ny{m.n_y}-Nb{m.n_beam}-Nm{m.n_mortar}')


def meshes() -> tuple[Mesh,...]:
    joint=(Mesh(16,8,64,8),Mesh(32,16,128,16),
           Mesh(64,32,256,32),Mesh(128,64,512,64))
    one_axis=(tuple(Mesh(64,32,256,n) for n in (16,64))+
              tuple(Mesh(64,32,n,32) for n in (128,512))+
              tuple(Mesh(n,32,256,32) for n in (32,128))+
              tuple(Mesh(64,n,256,32) for n in (16,64)))
    all_meshes=joint+one_axis
    if len(all_meshes)!=12 or len(set(all_meshes))!=12:
        raise AssertionError('duplicate or missing proposed reference mesh')
    return all_meshes


def cases() -> tuple[Case,...]:
    result=tuple(Case(mesh,topology,loading,law)
                 for mesh in meshes()
                 for topology in ('Q4','CST')
                 for loading in ('smooth','sine')
                 for law in ('P0','P1'))
    if len(result)!=96 or len({case.identity for case in result})!=96:
        raise AssertionError('duplicate or missing proposed reference case')
    return result


def structural_counts(mesh: Mesh, topology: str, law: str) -> dict[str,int]:
    """Combinatorial upper-size estimate, not measured resource usage."""
    if topology not in ('Q4','CST','CST-CB') or law not in ('P0','P1'):
        raise ValueError('unknown reference formulation')
    nodes=(2*mesh.n_s+1)*(mesh.n_y+1)
    shell_elements=(2 if topology=='Q4' else 4)*mesh.n_s*mesh.n_y
    multiplier=3*(mesh.n_mortar+(law=='P1'))
    return dict(shell_nodes=nodes,shell_elements=shell_elements,
                beam_elements=mesh.n_beam,shell_dofs=2*nodes,
                beam_dofs=6*mesh.n_beam+4,
                multiplier_dofs=multiplier,
                kkt_dimension=2*nodes+6*mesh.n_beam+4+multiplier)
