from pathlib import Path

import astropy.units as u
import numpy as np

from ppdmod import custom_components
from ppdmod import data
from ppdmod import fitting
from ppdmod import model
from ppdmod import plot
from ppdmod import utils
from ppdmod.parameter import STANDARD_PARAMETERS, Parameter
from ppdmod.options import OPTIONS


# NOTE: Turns off numpys automated parellelization.
# os.environ["OMP_NUM_THREADS"] = "1"

# TODO: Check wavelength axis for opacity interpolation.
data.set_fit_wavelengths([3.520375, 10.001093]*u.um)
path = Path("/Users/scheuck/Data/reduced_data/hd142666/matisse")
fits_files = [
    "hd_142666_2022-04-21T07_18_22:2022-04-21T06_47_05_HAWAII-2RG_FINAL_TARGET_INT.fits",
    "hd_142666_2022-04-21T07_18_22:2022-04-21T06_47_05_AQUARIUS_FINAL_TARGET_INT.fits",
    "hd_142666_2022-04-23T03_05_25:2022-04-23T02_28_06_HAWAII-2RG_FINAL_TARGET_INT.fits",
    "hd_142666_2022-04-23T03_05_25:2022-04-23T02_28_06_AQUARIUS_FINAL_TARGET_INT.fits"]
fits_files = list(map(lambda x: path / x, fits_files))
data.set_data(fits_files)

wavelength_axes = list(
    map(lambda x: data.ReadoutFits(x).wavelength, fits_files))
wavelength_axes = np.sort(np.unique(np.concatenate(wavelength_axes)))

flux_file = Path("/Users/scheuck/Data/flux_data/hd142666/HD142666_stellar_model.txt.gz")
wavelength, flux = np.loadtxt(flux_file, comments="#", unpack=True)[:2]
matisse_flux = utils.opacity_to_matisse_opacity(
    wavelength_axes, wavelength_grid=wavelength*u.um, opacity=flux*u.Jy).value*u.Jy
star_flux = Parameter(**STANDARD_PARAMETERS["f"])
star_flux.value, star_flux.wavelength = matisse_flux, wavelength_axes

weights = np.array([42.8, 9.7, 43.5, 1.1, 2.3, 0.6])/100
qval_file_dir = Path("/Users/scheuck/Data/opacities/QVAL")
qval_files = ["Q_Am_Mgolivine_Jae_DHS_f1.0_rv0.1.dat",
              "Q_Am_Mgolivine_Jae_DHS_f1.0_rv1.5.dat",
              "Q_Am_Mgpyroxene_Dor_DHS_f1.0_rv1.5.dat",
              "Q_Fo_Suto_DHS_f1.0_rv0.1.dat",
              "Q_Fo_Suto_DHS_f1.0_rv1.5.dat",
              "Q_En_Jaeger_DHS_f1.0_rv1.5.dat"]
qval_paths = list(map(lambda x: qval_file_dir / x, qval_files))
opacity = utils.linearly_combine_opacities(
    weights, qval_paths, wavelength_axes)
continuum_opacity = utils.opacity_to_matisse_opacity(
    wavelength_axes, qval_file=qval_file_dir / "Q_amorph_c_rv0.1.dat")

kappa_abs = Parameter(**STANDARD_PARAMETERS["kappa_abs"])
kappa_abs.value, kappa_abs.wavelength = opacity, wavelength_axes
kappa_cont = Parameter(**STANDARD_PARAMETERS["kappa_cont"])
kappa_cont.value, kappa_cont.wavelength = continuum_opacity, wavelength_axes

fov, pixel_size = 220, 0.1
dim = utils.get_next_power_of_two(fov / pixel_size)
distance = 148.3

OPTIONS["model.constant_params"] = {
    "dim": dim, "dist": distance, "eff_temp": 7500,
    "f": star_flux, "pixel_size": pixel_size,
    "eff_radius": 1.75, "inner_temp": 1500,
    "kappa_abs": kappa_abs, "kappa_cont": kappa_cont}

rin = Parameter(**STANDARD_PARAMETERS["rin"])
rout = Parameter(**STANDARD_PARAMETERS["rout"])

rin.value = 1.
rout.value = 7.

rin.set(min=0.5, max=3)
rout.set(min=1., max=4)
rout.free = True

inner_ring = {"rin": rin, "rout": rout}
inner_ring_labels = [f"ir_{label}" for label in inner_ring]

rin = Parameter(**STANDARD_PARAMETERS["rin"])
a = Parameter(**STANDARD_PARAMETERS["a"])
phi = Parameter(**STANDARD_PARAMETERS["phi"])

rin.value = 13
a.value = 0.5
phi.value = 130

rin.set(min=4, max=30)
a.set(min=0., max=1.)
phi.set(min=0, max=360)

outer_ring = {"rin": rin, "a": a, "phi": phi}
outer_ring_labels = [f"or_{label}" for label in outer_ring]

p = Parameter(**STANDARD_PARAMETERS["p"])
pa = Parameter(**STANDARD_PARAMETERS["pa"])
elong = Parameter(**STANDARD_PARAMETERS["elong"])
cont_weight = Parameter(**STANDARD_PARAMETERS["cont_weight"])
inner_sigma = Parameter(**STANDARD_PARAMETERS["inner_sigma"])

p.value = 0.5
pa.value = 145
elong.value = 0.5
cont_weight.value = 130
inner_sigma.value = 1e-3

p.set(min=0., max=1.)
pa.set(min=0, max=360)
elong.set(min=0, max=1)
cont_weight.set(min=0., max=1.)
inner_sigma.set(min=0, max=1e-2)

OPTIONS["model.shared_params"] = {"p": p, "pa": pa, "elong": elong,
                                  "inner_sigma": inner_sigma,
                                  "cont_weight": cont_weight}
shared_params_labels = [f"sh_{label}"
                        for label in OPTIONS["model.shared_params"]]

OPTIONS["model.components_and_params"] = [
    ["Star", {}],
    ["SymmetricSDGreyBodyContinuum", inner_ring],
    ["AsymmetricSDGreyBodyContinuum", outer_ring],
]
labels = inner_ring_labels + outer_ring_labels + shared_params_labels

wavelength = OPTIONS["fit.wavelengths"][-1]
results_dir = Path("")
components = custom_components.assemble_components(
    OPTIONS["model.components_and_params"], OPTIONS["model.shared_params"])
# m = model.Model(components)
# image = m.calculate_image(4096, 0.1, wavelength)
# fits_filename = results_dir / "model_init.fits"
# hdu = fits.PrimaryHDU(image.value)
# hdu.writeto(fits_filename, overwrite=True)
# plot.plot_model(4096, 0.1, m, wavelength, zoom=50, savefig=results_dir / "model_init.pdf")

theta = np.load(results_dir / "best_fit_params.npy")
components_and_params, shared_params = fitting.set_params_from_theta(theta)
components = custom_components.assemble_components(
    components_and_params, shared_params)

# HACK: This is to include innermost radius for rn.
innermost_radius = components[1].params["rin"]
for component in components:
    component.params["rin0"] = innermost_radius

new_params = dict(zip(labels, theta))
m = model.Model(components)
# plot.save_model_fits(dim, pixel_size, distance,
#                      new_params["sh_pa"], new_params["sh_elong"],
#                      m, wavelength, savefits=results_dir / "model.fits")
OPTIONS["plot.color.background"] == "black"
plot.plot_fit(new_params["sh_elong"], new_params["sh_pa"],
              savefig=results_dir / "fit_results.png")