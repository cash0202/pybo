from mwhutils.random import rstate
import numpy as np
import pybo
import reggie as rg


__all__ = ['init_model']


def init_model(f, bounds, design='latin', ninit=None, rng=None):
    """Initialize model and its hyperpriors using initial data.

    Arguments:
        f: function handle
        bounds: list of doubles (xmin, xmax) for each dimension.
        mean: str name of the mean class.
        mean_args: dict of arguments to be passed to the mean constructor.
        seed: int representing the random seed for reproducibility.

    Returns:
        Initialized model.
    """
    rng = rstate(rng)
    xmin, xmax = bounds.T
    ninit = 3 * len(xmin) if ninit is None else ninit

    # get initial design
    init_design = getattr(pybo.inits, 'init_' + design)
    xinit = init_design(bounds, ninit, rng)
    yinit = np.fromiter((f(xi) for xi in xinit), dtype=np.float)

    # define initial setting of hyper parameters
    sn2 = 1e-6
    rho = yinit.max() - yinit.min() if (len(yinit) > 1) else 1.
    rho = 1. if (rho < 1e-1) else rho
    ell = 0.25 * (xmax - xmin)
    bias = np.mean(yinit) if (len(yinit) > 0) else 0.

    # initialize the base model
    model = rg.make_gp(sn2, rho, ell, bias, inference='exact')

    # define priors
    model.params['like.sn2'].set_prior('lognormal', mu=-2, s2=1)
    model.params['kern.rho'].set_prior('lognormal', mu=np.log(rho), s2=1.)
    model.params['kern.ell'].set_prior('uniform', ell / 100, ell * 10)
    model.params['mean.bias'].set_prior('normal', bias, rho)


    # initialize the MCMC inference meta-model and add data
    model = rg.MCMC(model, n=10, burn=100, rng=rng)
    model.add_data(xinit, yinit)

    return model
