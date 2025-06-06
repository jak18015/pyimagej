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
import xarray as xr
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
    img         : ImageJ2 image object
    iterations  : number of iterations for the deconvolution
    reg         : regularization factor
    na          : numerical aperture of the objective lens
    wv          : wavelength of the light used for imaging (in nm)
    ri_immersion: refractive index of the immersion medium
    ri_sample   : refractive index of the sample
    lat_res     : lateral resolution (i.e. xy) (in um)
    ax_res      : axial resolution (i.e. z) (in um)
    pz          : distance away from coverslip (in um)
    
    Returns
    dimg        : deconvolved image
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
    dimg = ij.op().deconvolve().richardsonLucyTV(img_f, psf, iterations, reg)

    return dimg


def process(wd, image):
    """
    Processes a single image by deconvolving it and saving the result.

    Parameters
    image : str
        The filename of the image to be processed.
    """
    print(f"Processing image: {image}")
    img = ij.io().open(os.path.join(wd, image))
    dump_info(img)  # print image info
    img = ij.op().convert().float32(img)
    decon_channels = []  # list to hold deconvolved channels
    for channel in range(img.shape[2]):
        if img.ndim == 3:
            decon = deconvolve(img[:,:,channel], wavelength[channel], iterations, reg, na, ri_sample, ri_immersion, lat_res, ax_res, pz)
        elif img.ndim == 4:
            decon = deconvolve(img[:,:,channel,:], wavelength[channel], iterations, reg, na, ri_sample, ri_immersion, lat_res, ax_res, pz)
        decon = ij.py.from_java(decon)
        decon_channels.append(decon)
    decon_ximg = np.stack(decon_channels, axis=1)
    # switch the row and col dimensions
    # decon_ximg = np.transpose(decon_ximg, (0, 1, 3, 2))  # (pln, ch, col, row)
    decon_ximg = xr.DataArray(decon_ximg, name='decon_ximg', dims=('pln', 'ch', 'row', 'col'))
    decon_img = ij.py.to_java(decon_ximg)
    dump_info(decon_img)

    return decon_img

def save_image (dir, img_name, decon_img, iterstring, reg):
    """ Saves the deconvolved image to the specified directory with a specific naming convention.
    If a file with the same name already exists, it is removed before saving the new image.
    """
    if os.path.exists(os.path.join(dir, f'{img_name[:-4]}-decon-{iterstring}-iteration-{reg}-reg.tif')):
        os.remove(os.path.join(dir, f'{img_name[:-4]}-decon-{iterstring}-iteration-{reg}-reg.tif'))
        print(f'Removed existing file: {img_name[:-4]}-decon-{iterstring}-iteration-{reg}-reg.tif')
        ij.io().save(decon_img, os.path.join(dir, f'{img_name[:-4]}-decon-{iterstring}-iteration-{reg}-reg.tif'))
        print(f'Saved deconvolved image: {img_name[:-4]}-decon-{iterstring}-iteration-{reg}-reg.tif')
    else:
        ij.io().save(decon_img, os.path.join(dir, f'{img_name[:-4]}-decon-{iterstring}-iteration-{reg}-reg.tif'))
        print(f'Saved deconvolved image: {img_name[:-4]}-decon-{iterstring}-iteration-{reg}-reg.tif')

# -------------------------------------------------
# SETUP
# -------------------------------------------------

# initialize ImageJ2
# make sure to run this in a conda environment with pyimagej installed
sj.config.add_option('-Xmx6g')
ij = imagej.init(add_legacy=False)
print(f"ImageJ2 version: {ij.getVersion()}")

# import imagej2 and imglib2 Java classes
CreateNamespace = imagej.sj.jimport('net.imagej.ops.create.CreateNamespace')
FinalDimensions = imagej.sj.jimport('net.imglib2.FinalDimensions')
FloatType = imagej.sj.jimport('net.imglib2.type.numeric.real.FloatType')

# Richardson-Lucy TV parameters
iterations = 1 # number of iterations for deconvolution
reg = 0.002 # regularization factor
na = 1.5 # numerical aperture
wavelength = [647, 594, 488, 405] # emission wavelength
ri_immersion = 1 # refractive index (immersion)
ri_sample = 1 # refractive index (sample)
lat_res = 0.07 # lateral resolution (i.e. xy)
ax_res = 1 # axial resolution (i.e. z)
pz = 0 # distance away from coverslip

iterstring = f"{iterations:02}"
wd = input("enter the directory with images:\n").strip()
img_list = [f for f in os.listdir(wd) if f.lower().endswith('.tif')]
print(".tif files found:")
for img in img_list:
    print(f" - {img}")
img = input("enter the filename to deconvolve:\n").strip()
print('\n')
title  = img[:-4]  # remove the .tif extension
decon_img = process(wd, img)
save_image(wd, img, decon_img, iterstring, reg)
ij.dispose() # close the ImageJ instance