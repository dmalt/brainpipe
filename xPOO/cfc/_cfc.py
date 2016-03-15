import numpy as n
from itertools import product
from joblib import Parallel, delayed

from brainpipe.xPOO._utils._system import (groupInList, list2index,
                                           adaptsize)
from brainpipe.xPOO.cfc.methods import *

__all__ = [
            '_cfcCheck',
            '_cfcPvalue',
            '_cfcFilt',
            '_cfcFiltSuro'
          ]


def _cfcFilt(xPha, xAmp, self):
    """SUP: get only the cfc from the subfunction _cfcFiltSub
    """
    # Get the unormalized cfc :
    _, _, uCfc = _cfcFiltSub(xPha, xAmp, self)

    return uCfc


def _cfcFiltSuro(xPha, xAmp, surJob, self):
    """SUP: Get the cfc and surrogates

    The function return:
        - The unormalized cfc
        - All the surrogates (for pvalue)
        - The mean of surrogates (for normalization)
        - The deviation of surrogates (for normalization)
    """
    # Get the unormalized cfc :
    xPha, xAmp, uCfc = _cfcFiltSub(xPha, xAmp, self)

    # Run surogates on each window :
    Suro = Parallel(n_jobs=surJob)(delayed(_cfcGetSuro)(
        xPha[:, k[0]:k[1], :], xAmp[:, k[0]:k[1], :],
        self.Id, self.n_perm, self.nbins) for k in self.window)
    mSuro = [n.mean(k, 3) for k in Suro]
    stdSuro = [n.std(k, 3) for k in Suro]

    return uCfc, Suro, mSuro, stdSuro


def _cfcFiltSub(xPha, xAmp, self):
    """SUB: get the phase, amplitude and the asociated cfc
    """
    # Check input variables :
    npts, ntrial = xPha.shape
    W = self.window
    nwin = len(W)

    # Get the filter for phase/amplitude properties :
    phaMeth = self.pha.get(self._sf, self.pha.f, self._npts)
    ampMeth = self.amp.get(self._sf, self.amp.f, self._npts)

    # Filt the phase and amplitude :
    xPha = self.pha.apply(xPha, phaMeth)
    xAmp = self.amp.apply(xAmp, ampMeth)

    # 2D loop trick :
    claIdx, listWin, listTrial = list2index(nwin, ntrial)

    # Get the cfc :
    uCfc = [_cfcGet(n.squeeze(xPha[:, W[k[0]][0]:W[k[0]][1], k[1]]),
                    n.squeeze(xAmp[:, W[k[0]][0]:W[k[0]][1], k[1]]),
                    self.Id, self.nbins) for k in claIdx]

    return xPha, xAmp, n.array(groupInList(uCfc, listWin))


def _cfcGet(pha, amp, Id, nbins):
    """Compute the basic cfc model
    """
    # Get the cfc model :
    Model, _, _, _, _, _ = CfcSettings(Id, nbins=nbins)

    return Model(n.matrix(pha), n.matrix(amp), nbins)


def _cfcGetSuro(pha, amp, Id, n_perm, nbins):
    """Compute the basic cfc model
    """
    # Get the cfc model :
    Model, Sur, _, _, _, _ = CfcSettings(Id, nbins=nbins)

    return Sur(pha, amp, Model, n_perm)


def _cfcCheck(x, xPha, xAmp, npts):
    """Manage x, xPha and xAmp size
    """
    if xPha is None and xAmp is None:
        if len(x.shape) == 2:
            x = x[n.newaxis, ...]
        if x.shape[1] != npts:
            raise ValueError('Second dimension must be '+str(npts))
        xPha, xAmp = x, x
    else:
        if xPha.shape == xAmp.shape:
            if len(xPha.shape) == 2:
                xPha = xPha[n.newaxis, ...]
                xAmp = xAmp[n.newaxis, ...]
            if xPha.shape[1] != npts:
                raise ValueError('Second dimension must be '+str(npts))
        else:
            raise ValueError('xPha and xAmp must have the same size')

    return xPha, xAmp


def _cfcPvalue(nCfc, perm):
    """Get the pvalue of the cfc using permutations
    """
    nW, nT, nA, nP = nCfc.shape
    nperm = perm[0].shape[3]
    pvalue = n.ones(nCfc.shape)
    for i, j, k, l in product(range(nW), range(nT), range(nA), range(nP)):
        data = nCfc[i, j, k, l]
        permD = perm[i][j, k, l, :]
        pv = (n.sum(permD >= data)) / nperm
        if pv == 0:
            pvalue[i, j, k, l] = 1/nperm
        else:
            pvalue[i, j, k, l] = pv
    return pvalue