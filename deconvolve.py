# This script deconvolves a 3D image using the Richardson-Lucy algorithm with TV regularization.
# It should be ran from a pyimagej conda environment (see https://py.imagej.net/en/latest/index.html)
# It uses the ImageJ2 library and requires Java 8 or higher.
# The script processes all TIFF images in the current working directory, excluding those that have already been deconvolved.
# The deconvolution parameters are set in the SETUP section of the script.
# The script processes each image slice by slice, deconvolving each slice separately.
# The deconvolved slices are then stacked back together to form a 3D image.
# The deconvolved image is saved in the same directory as the original image with a '-deconvolved' suffix.

# -------------------------------------------------
# DEPENDENCIES
# -------------------------------------------------

import imagej
import matplotlib.pyplot as plt
import scyjava as sj
import numpy as np
import os

# -------------------------------------------------
# FUNCTIONS
# -------------------------------------------------
def dump_info(image):
    """A handy function to print details of an image object."""
    name = image.name if hasattr(image, 'name') else None # xarray
    if name is None and hasattr(image, 'getName'): name = image.getName() # Dataset
    if name is None and hasattr(image, 'getTitle'): name = image.getTitle() # ImagePlus
    print(f" name: {name or 'N/A'}")
    print(f" type: {type(image)}")
    print(f"dtype: {image.dtype if hasattr(image, 'dtype') else 'N/A'}")
    print(f"shape: {image.shape}")
    print(f" dims: {image.dims if hasattr(image, 'dims') else 'N/A'}")


def deconvolve(img, wv, iterations, reg, na, ri_sample, ri_immersion, lat_res, ax_res, pz):
    """
    Deconvolves a 3D image using the Richardson-Lucy algorithm with TV regularization.

    Parameters
    img         : 3D image to be deconvolved
    wv          : wavelength of the light used for imaging (in nm)
    iterations  : number of iterations for the deconvolution
    reg         : regularization factor
    na          : numerical aperture of the objective lens
    ri_sample   : refractive index of the sample
    ri_immersion: refractive index of the immersion medium
    lat_res     : lateral resolution (i.e. xy) (in um)
    ax_res      : axial resolution (i.e. z) (in um)
    pz          : distance away from coverslip (in um)
    
    Returns
    img_decon   : deconvolved image
    """
    img_f = ij.py.to_java(img)
   # convert input parameters into meters
    wv = wv * 1E-9
    lat_res = lat_res * 1E-6
    ax_res = ax_res * 1E-6
    pz = pz * 1E-6
   # convert the input image dimensions to imglib2 FinalDimensions
    psf_dims = FinalDimensions(img.shape)
    # create synthetic PSF
    psf = ij.op().namespace(CreateNamespace).kernelDiffraction(
        psf_dims, na, wv, ri_sample, ri_immersion, lat_res, ax_res, pz, FloatType())
    # deconvolve the image using Richardson-Lucy with TV regularization
    img_decon = ij.op().deconvolve().richardsonLucyTV(img_f, psf, iterations, reg)

    return img_decon


def process(wd, image):
    """
    Processes a single image by deconvolving it and saving the result.

    Parameters
    image : str
        The filename of the image to be processed.
    """
    print(f"Processing image: {image}")
    title = image[:-4]
    img = ij.io().open(os.path.join(wd, image))
    dump_info(img)  # print image info
    img = ij.op().convert().float32(img)
    decon_slices = []
    for i in range(img.shape[2]):
        slice_img = img[:, :, i, :]
        wv = wavelength[i]
        print(f"Deconvolving channel {i+1}/{img.shape[2]} with wavelength {wv} nm")
        img_decon = deconvolve(slice_img, wv, iterations, reg, na, ri_sample, ri_immersion, lat_res, ax_res, pz)
        decon_slices.append(img_decon)
    img_decon = Views.stack(decon_slices)
    # stacked_py = ij.py.from_java(img_decon)
    # dump_info(stacked_py)
    # img_decon = ij.py.to_dataset(stacked_py, dim_order=['z', 'ch', 'y', 'x'])
    # img_decon.axis(0).setType(ij.axis.Axes.Z)
    # img_decon.axis(1).setType(ij.axis.Axes.CHANNEL)
    # img_decon.axis(2).setType(ij.axis.Axes.Y)
    # img_decon.axis(3).setType(ij.axis.Axes.X)
    dump_info(img_decon)
    output_title = title + '-deconvolved.ome.tif'
    if os.path.exists(f'{wd}/{output_title}'):
        os.remove(f'{wd}/{output_title}')
    print(f"Removed existing file: {output_title}")
    ij.io().save(img_decon, f"{wd}/{output_title}")
    print(f"Saved deconvolved image as {output_title}")

# -------------------------------------------------
# SETUP
# -------------------------------------------------

sj.config.add_option('-Xmx6g') # set the maximum heap size to 6 GB
ij = imagej.init(add_legacy=False) # initialize ImageJ2
print(f"ImageJ2 version: {ij.getVersion()}")
print(ij.getApp().getInfo(True)) # print ImageJ2 info

# import imagej2 and imglib2 Java classes
CreateNamespace = imagej.sj.jimport('net.imagej.ops.create.CreateNamespace')
FinalDimensions = imagej.sj.jimport('net.imglib2.FinalDimensions')
FloatType = imagej.sj.jimport('net.imglib2.type.numeric.real.FloatType')
Views = sj.jimport('net.imglib2.view.Views')

iterations = 30 # number of iterations
reg = 0.002 # regularization factor``
na = 1.4 # numerical aperture
wavelength = [617, 594, 508, 461] # emission wavelengths (in nm)
ri_immersion = 1.5 # refractive index (immersion)
ri_sample = 1.4 # refractive index (sample)
lat_res = 0.07 # lateral resolution (i.e. xy)
ax_res = 0.24 # axial resolution (i.e. z)
pz = 0 # distance away from coverslip

# -------------------------------------------------
# MAIN
# -------------------------------------------------

# wd = input("enter the directory with images:\n").strip()
wd = '/Users/jkellerm/Library/CloudStorage/OneDrive-MichiganMedicine/0-active-projects/expansion/expansion_20250605_nikon/'
img = 'nd010-1.tif'
# img_list = [f for f in os.listdir(wd) if f.lower().endswith('.tif') or f.lower().endswith('.tiff')]
# print("TIFF images found:")
# for img in img_list:
    # print(f" - {img}")
# img = input("enter the image to deconvolve:\n").strip()
process(wd, img)
ij.dispose() # close the ImageJ instance