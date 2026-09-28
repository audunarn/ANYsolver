"""Independent re-implementation (no ANYsolver code) of the D1 guided-strip
scalar obstacle problem: Q1 FE + clipped Q1 mortar pressure vs cell-centred FV.
-D Lap w = -q + p on [0,1]^2, w=0 at x=0, natural elsewhere,
w >= -g0 on y <= yr (obstacle support), p >= 0.
"""
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spla

E, NU, T = 1e5, 0.3, 0.05
D = 5/6*E*T/(2*(1+NU))
Q = 0.3
G0 = 4e-5
YR = 0.9

def mass1d(n, clip=1.0, nodes=None):
    """1D linear FE mass on [0,1] (n cells), integration clipped to [0,clip]."""
    x = np.linspace(0, 1, n+1) if nodes is None else nodes
    M = np.zeros((len(x), len(x)))
    gp = np.array([0.5-0.5/np.sqrt(3), 0.5+0.5/np.sqrt(3)])
    for c in range(len(x)-1):
        a, b = x[c], min(x[c+1], clip)
        if b <= a: continue
        h = x[c+1]-x[c]
        for s in gp:
            y = a + s*(b-a)
            loc = (y-x[c])/h
            N = np.array([1-loc, loc])
            M[c:c+2, c:c+2] += 0.5*(b-a)*np.outer(N, N)
    return M

def stiff1d(n, nodes=None):
    x = np.linspace(0, 1, n+1) if nodes is None else nodes
    K = np.zeros((len(x), len(x)))
    for c in range(len(x)-1):
        h = x[c+1]-x[c]
        K[c:c+2, c:c+2] += np.array([[1, -1], [-1, 1]])/h
    return K

def bin_integrals_1d(n, nbins, clip=1.0, nodes=None, edges=None):
    """I[b, i] = int_{bin_b ∩ [0,clip]} phi_i  (exact for hat functions)."""
    x = np.linspace(0, 1, n+1) if nodes is None else nodes
    e = np.linspace(0, 1, nbins+1) if edges is None else edges
    I = np.zeros((len(e)-1, len(x)))
    for c in range(len(x)-1):
        h = x[c+1]-x[c]
        for b in range(len(e)-1):
            a = max(x[c], e[b]); z = min(x[c+1], e[b+1], clip)
            if z <= a: continue
            mid = 0.5*(a+z); loc = (mid-x[c])/h
            I[b, c] += (z-a)*(1-loc); I[b, c+1] += (z-a)*loc
    return I

def solve_q1(nx, ny, ynodes=None, merge_cut=False):
    """Q1 FE with Q1 clipped mortar pressure on the same mesh (source-only)."""
    xn = np.linspace(0, 1, nx+1)
    yn = np.linspace(0, 1, ny+1) if ynodes is None else np.asarray(ynodes)
    Kx, Mx = stiff1d(nx, xn), mass1d(nx, 1.0, xn)
    Ky, My = stiff1d(len(yn)-1, yn), mass1d(len(yn)-1, 1.0, yn)
    K = (D*(sp.kron(sp.csr_matrix(My), sp.csr_matrix(Kx)) + sp.kron(sp.csr_matrix(Ky), sp.csr_matrix(Mx)))).tocsr()
    f = -Q*np.kron(My.sum(1), Mx.sum(1))
    Myc = mass1d(len(yn)-1, YR, yn)
    B = sp.kron(sp.csr_matrix(Myc), sp.csr_matrix(Mx)).tocsr()
    S = np.asarray(B.sum(1)).ravel()
    sup = S > 1e-14
    P = sp.eye(len(S), format='csr')[np.flatnonzero(sup)]
    if merge_cut:
        # boundary modification: pressure nodes whose y-support is clipped
        # (partially outside obstacle) are merged into the next interior row.
        ny1 = len(yn)
        rowsup = Myc.sum(1)/np.maximum(My.sum(1), 1e-300)
        cut_rows = [j for j in range(ny1) if 0 < rowsup[j] < 1-1e-12 and yn[j] > YR - 1e-12]
        keep_rows = [j for j in range(ny1) if rowsup[j] > 0 and j not in cut_rows]
        Pr = np.zeros((len(keep_rows), ny1))
        for r, j in enumerate(keep_rows):
            Pr[r, j] = 1.0
        for j in cut_rows:
            target = max(k for k in keep_rows if yn[k] < yn[j])
            Pr[keep_rows.index(target), j] = 1.0
        P = sp.kron(sp.csr_matrix(Pr), sp.eye(nx+1)).tocsr()
    Bp = (P @ B).tocsr()
    Sp = np.asarray(Bp.sum(1)).ravel()
    free = np.ones(len(f), bool); free[np.arange(0, len(f), nx+1)] = False  # x=0 nodes
    Kf = K[free][:, free].tocsc()
    lu = spla.splu(Kf)
    Bf = Bp[:, free]
    u0 = lu.solve(f[free])
    R = lu.solve(Bf.T.toarray())
    M = np.asarray(Bf @ R); M = 0.5*(M+M.T)
    r = Bf @ u0 + G0*Sp
    lam = pdas_lcp(M, r, Sp)
    u = np.zeros(len(f)); u[free] = u0 + R @ lam
    pnode = P.T @ lam                 # nodal pressure in original Q1 basis (Pa)
    Gw = Bp @ u + G0*Sp
    res = Kf @ u[free] - f[free] - Bf.T @ lam
    return dict(nx=nx, ny=len(yn)-1, xn=xn, yn=yn, p=pnode.reshape(len(yn), nx+1),
                w=u.reshape(len(yn), nx+1), reaction=float(Sp @ lam),
                min_wgap=float(np.min(Gw/Sp)), eq=float(np.linalg.norm(res)),
                comp=float(np.max(np.abs(lam*Gw/Sp))))

def pdas_lcp(M, r, S, maxit=500):
    """Solve M lam + r >= 0, lam >= 0, complementarity (PDAS + certification)."""
    n = len(r)
    A = (r < 0)
    lam = np.zeros(n)
    c = 1.0/np.max(np.diag(M))
    for it in range(maxit):
        lam = np.zeros(n)
        if A.any():
            lam[A] = np.linalg.solve(M[np.ix_(A, A)], -r[A])
        g = M @ lam + r
        Anew = (lam - c*g) > 0
        if np.array_equal(Anew, A):
            break
        A = Anew
    else:
        raise RuntimeError("PDAS did not settle")
    # certificate
    g = M @ lam + r
    assert lam.min() >= -1e-12*max(1, lam.max()), lam.min()
    assert (g/S).min() >= -1e-12, (g/S).min()
    return np.maximum(lam, 0)

def solve_fv(nx, ny):
    dx, dy = 1/nx, 1/ny
    n = nx*ny
    rows, cols, vals = [], [], []
    diag = np.zeros(n)
    def edge(a, b, c):
        diag[a] += c; diag[b] += c
        rows.extend((a, b)); cols.extend((b, a)); vals.extend((-c, -c))
    for j in range(ny):
        for i in range(nx):
            k = j*nx+i
            if i == 0: diag[k] += 2*D*dy/dx
            if i+1 < nx: edge(k, k+1, D*dy/dx)
            if j+1 < ny: edge(k, k+nx, D*dx/dy)
    K = sp.csr_matrix((vals+list(diag), (rows+list(range(n)), cols+list(range(n)))), shape=(n, n))
    f = np.full(n, -Q*dx*dy)
    obst = np.repeat(((np.arange(ny)+0.5)*dy < YR), nx)
    # PDAS for bound constraint w >= -G0 on obstacle cells (M-matrix -> monotone)
    w = spla.spsolve(K.tocsc(), f)
    A = obst & (w < -G0)
    for it in range(1000):
        Fr = ~A
        w = np.full(n, -G0);
        rhs = f[Fr] - K[Fr][:, A] @ w[A]
        w[Fr] = spla.spsolve(K[Fr][:, Fr].tocsc(), rhs)
        reac = K @ w - f
        Anew = obst & ((A & (reac > 0)) | (~A & (w < -G0)))
        if np.array_equal(Anew, A): break
        A = Anew
    reac = K @ w - f
    pf = np.where(A, reac, 0.0)
    assert (w[obst] + G0).min() > -1e-12 and pf.min() > -1e-12
    return dict(nx=nx, ny=ny, force=pf.reshape(ny, nx), w=w.reshape(ny, nx),
                reaction=float(pf.sum()), eq=float(abs(np.abs(reac[~A]).max())))

def q1_bins(sol, bx_edges, by_edges):
    Ix = bin_integrals_1d(sol['nx'], len(bx_edges)-1, 1.0, sol['xn'], bx_edges)
    Iy = bin_integrals_1d(sol['ny'], len(by_edges)-1, YR, sol['yn'], by_edges)
    return Iy @ sol['p'] @ Ix.T

def fv_bins(fv, bx_edges, by_edges):
    nx, ny = fv['nx'], fv['ny']
    xc = (np.arange(nx)+0.5)/nx; yc = (np.arange(ny)+0.5)/ny
    bi = np.searchsorted(bx_edges, xc, side='right')-1
    bj = np.searchsorted(by_edges, yc, side='right')-1
    out = np.zeros((len(by_edges)-1, len(bx_edges)-1))
    np.add.at(out, (bj[:, None], bi[None, :]), fv['force'])
    return out

def l2rel(a, b): return np.linalg.norm(a-b)/np.linalg.norm(b)


# ---------------------------------------------------------------------------
# Review checks (run: python d1_rim_oracle.py)  ~1-2 min, <1 GB
# ---------------------------------------------------------------------------
def _uzawa_and_ssn(nx, ny, k=1.0e4):
    xn = np.linspace(0, 1, nx+1); yn = np.linspace(0, 1, ny+1)
    Kx, Mx = stiff1d(nx, xn), mass1d(nx, 1.0, xn); Ky, My = stiff1d(ny, yn), mass1d(ny, 1.0, yn)
    K = (D*(sp.kron(sp.csr_matrix(My), sp.csr_matrix(Kx)) + sp.kron(sp.csr_matrix(Ky), sp.csr_matrix(Mx)))).tocsr()
    f = -Q*np.kron(My.sum(1), Mx.sum(1))
    B = sp.kron(sp.csr_matrix(mass1d(ny, YR, yn)), sp.csr_matrix(Mx)).tocsr()
    S = np.asarray(B.sum(1)).ravel(); sup = np.flatnonzero(S > 1e-14); B = B[sup]; S = S[sup]
    free = np.ones(len(f), bool); free[np.arange(0, len(f), nx+1)] = False
    Kf = K[free][:, free]; Bf = B[:, free]; ff = f[free]
    lu = spla.splu(Kf.tocsc())
    M = np.asarray(Bf @ lu.solve(Bf.T.toarray())); M = 0.5*(M+M.T)
    lam = pdas_lcp(M, Bf @ lu.solve(ff) + G0*S, S); A = lam > 1e-12
    mu = np.linalg.eigvals((M/S[:, None])[np.ix_(A, A)]).real
    rho = np.max(np.abs(1 - k*mu))
    # monolithic semismooth Newton (primal-dual active set) from a cold start
    n, m = Kf.shape[0], Bf.shape[0]; u = np.zeros(n); z = np.zeros(m); c = D*nx*nx
    for it in range(1, 200):
        g = (Bf @ u)/S + G0; act = (z - c*g) > 0
        KKT = sp.bmat([[Kf, -Bf[act].T], [sp.diags(1.0/S[act]) @ Bf[act], None]], format='csc')
        sol = spla.spsolve(KKT, np.r_[ff, -G0*np.ones(act.sum())])
        u = sol[:n]; z = np.zeros(m); z[act] = sol[n:]
        if np.array_equal((z - c*((Bf @ u)/S + G0)) > 0, act): break
    return k*mu.min(), k*mu.max(), rho, it, float(S @ z)

if __name__ == "__main__":
    import time
    t0 = time.time()
    fv = solve_fv(256, 320)
    print("FV256x320 reaction %.9f N (FV last supported cell row carries %.6f N = rim line load)"
          % (fv['reaction'], fv['force'][287].sum()))
    e16 = np.linspace(0, 1, 17); e8 = np.linspace(0, 1, 9)
    ey9 = np.r_[np.linspace(0, 0.9, 10), 1.0]          # support-aligned: obstacle edge is a bin edge
    R16 = fv_bins(fv, e16, e16); R169 = fv_bins(fv, e16, ey9); R89 = fv_bins(fv, e8, ey9)
    fv2 = solve_fv(128, 160)
    print("FV128x160 vs FV256x320: 16x16 bins %.3f%%, 16x9 support-aligned %.3f%%"
          % (100*l2rel(fv_bins(fv2, e16, e16), R16), 100*l2rel(fv_bins(fv2, e16, ey9), R169)))
    print("\nA. Bin-force L2 vs FV256x320 (source-only Q1 FE + clipped Q1 mortar pressure)")
    print("%-7s %-8s %-11s %-9s %-12s %-11s %s" % ("mesh", "rim-node", "16x16 orig", "rim-rows", "16x9 aligned", "8x9 aligned", "reaction N"))
    for nx, ny in ((4, 8), (16, 8), (16, 16), (32, 16), (32, 32), (16, 20), (32, 20), (32, 40), (64, 64), (64, 80)):
        s = solve_q1(nx, ny)
        b = q1_bins(s, e16, e16); d = b - R16
        print("%-7s %-8s %-11.2f %-9.1f %-12.2f %-11.2f %.9f" % (
            "%dx%d" % (nx, ny), "yes" if abs(0.9*ny - round(0.9*ny)) < 1e-9 else "no",
            100*l2rel(b, R16), 100*np.abs(d[13:15]).sum()/np.abs(d).sum(),
            100*l2rel(q1_bins(s, e16, ey9), R169), 100*l2rel(q1_bins(s, e8, ey9), R89), s['reaction']))
    print("\nB. Uzawa map spectrum (k=1e4 Pa/m) and monolithic SSN iterations on the same discrete problem")
    print("%-7s %-10s %-10s %-9s %-14s %-9s %s" % ("mesh", "k*mu_min", "k*mu_max", "rho", "augs for 1e-6", "SSN its", "reaction N"))
    for nx, ny in ((8, 1), (24, 1), (64, 1), (4, 8), (16, 20), (32, 40)):
        a, b, rho, its, R = _uzawa_and_ssn(nx, ny)
        print("%-7s %-10.2e %-10.2f %-9.5f %-14.0f %-9d %.9f" % ("%dx%d" % (nx, ny), a, b, rho, np.log(1e-6)/np.log(rho), its, R))
    print("\nC. Nodal pressure near the rim (x=0.9 column): interior p=q, rim spike ~ line load / h")
    for nx, ny in ((32, 40), (64, 80), (64, 64)):
        s = solve_q1(nx, ny); col = int(round(0.9*nx))
        rows = [k for k in range(len(s['yn'])) if 0.84 <= s['yn'][k] <= 0.93]
        print("%-6s " % ("%dx%d" % (nx, ny)) + " ".join("y=%.4f:%.3f" % (s['yn'][k], s['p'][k, col]) for k in rows))
    print("\ntotal %.0f s" % (time.time() - t0))
