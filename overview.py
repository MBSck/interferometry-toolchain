from pathlib import Path

import astropy.units as u
from matadrs.utils.plot import Plotter
from ppdmod.data import set_data
from ppdmod.plot import plot_overview
from ppdmod.options import OPTIONS


if __name__ == "__main__":
    fitting_dir = Path("/Users/scheuck/Data/reduced_data/hd142666/fitting_data")
    OPTIONS["fit.data"] = ["flux", "vis2", "t3phi"]
    OPTIONS["fit.wavelengths"] = [1.6, 2.25, 3.5, 8, 8.5,
                                  9, 10, 11.3, 12.5]*u.um
    OPTIONS["data.binning.window"] = 0.2
    # fits_files = list(fitting_dir.glob("*.fits"))
    # set_data(fits_files)
    # plot_overview(title="Data Overview",
    #               savefig="data_overview.pdf")
    # uv_plotter = Plotter(fits_files, plot_name="uv.pdf")
    # uv_plotter.add_uv(color_grouping="instrument",
    #                   make_tracks=True).plot(save=True)
    # ut_files = Path("/Users/scheuck/Data/reduced_data/hd142666/matisse/mat_tools/nband").glob("*INT.fits")
    # uv_plotter = Plotter(list(ut_files), plot_name="uv_uts.pdf")
    # uv_plotter.add_uv(color_grouping="file", make_tracks=True).plot(save=True)
    files = list(Path("/Users/scheuck/Data/reduced_data/hd142666/matisse/mat_tools/nband").glob("*INT.fits"))
    plotter = Plotter(files[0], plot_name="test.pdf")
    unwrap = True if "nband" in str(files[0]) else False
    plotter.add_mosaic(unwrap=unwrap).plot(error=True, save=True)
