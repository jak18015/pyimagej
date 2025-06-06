# deconvolution.py

import os
import numpy as np
import xarray as xr
import imagej
import scyjava as sj

# Java classes (imported globally for reuse)
CreateNamespace = None
FinalDimensions = None
FloatType = None

def setup_imagej(memory='6g'):
    """Initializes ImageJ and loads necessary Java classes."""
    global CreateNamespace, FinalDimensions, FloatType
    sj.config.add_option(f'-Xmx{memory}')
    ij = imagej.init(add_legacy=False)
    print(f"ImageJ2 version: {ij.getVersion()}")
    CreateNamespace = imagej.sj.jimport('net.imagej.ops.create.CreateNamespace')
    FinalDimensions = imagej.sj.jimport('net.imglib2.FinalDimensions')
    FloatType = imagej.sj.jimport('net.imglib2.type.numeric.real.FloatType')
    return ij


def dump_info(image):
    """Prints useful metadata about an image."""
    name = image.name if hasattr(image, 'name') else None
    if name is None and hasattr(image, 'getName'): name = image.getName()
    if name is None and hasattr(image, 'getTitle'): name = image.getTitle()
    print(f" name: {name or 'N/A'}")
    print(f" type: {type(image)}")
    print(f"dtype: {image.dtype if hasattr(image, 'dtype') else 'N/A'}")
    print(f"shape: {image.shape}")
    print(f" dims: {image.dims if hasattr(image, 'dims') else 'N/A'}")


def deconvolve(ij, img, wv, iterations, reg, na, ri_sample, ri_immersion, lat_res, ax_res, pz):
    """Applies Richardson-Lucy deconvolution with TV regularization."""
    img_f = ij.py.to_java(img)
    wv *= 1E-9
    lat_res *= 1E-6
    ax_res *= 1E-6
    pz *= 1E-6
    psf_dims = FinalDimensions(img.shape)
    psf = ij.op().namespace(CreateNamespace).kernelDiffraction(
        psf_dims, na, wv, ri_sample, ri_immersion, lat_res, ax_res, pz, FloatType())
    dimg = ij.op().deconvolve().richardsonLucyTV(img_f, psf, iterations, reg)
    return dimg


def process(ij, image_path, wavelengths, iterations, reg, na, ri_sample, ri_immersion, lat_res, ax_res, pz):
    """Loads and deconvolves each channel of an image."""
    print(f"Processing image: {image_path}")
    img = ij.io().open(image_path)
    dump_info(img)
    img = ij.op().convert().float32(img)
    decon_channels = []

    for channel in range(img.shape[2]):
        if img.ndim == 3:
            decon = deconvolve(ij, img[:, :, channel], wavelengths[channel], iterations, reg, na, ri_sample, ri_immersion, lat_res, ax_res, pz)
        elif img.ndim == 4:
            decon = deconvolve(ij, img[:, :, channel, :], wavelengths[channel], iterations, reg, na, ri_sample, ri_immersion, lat_res, ax_res, pz)
        decon = ij.py.from_java(decon)
        decon_channels.append(decon)

    decon_ximg = np.stack(decon_channels, axis=1)
    decon_ximg = xr.DataArray(decon_ximg, name='decon_ximg', dims=('pln', 'ch', 'row', 'col'))
    decon_img = ij.py.to_java(decon_ximg)
    dump_info(decon_img)
    return decon_img


def save_image(ij, output_dir, img_name, decon_img, iterstring, reg):
    """Saves the deconvolved image with a standardized filename."""
    filename = f'{img_name[:-4]}-decon-{iterstring}-iteration-{reg}-reg.tif'
    output_path = os.path.join(output_dir, filename)

    if os.path.exists(output_path):
        os.remove(output_path)
        print(f'Removed existing file: {filename}')
    ij.io().save(decon_img, output_path)
    print(f'Saved deconvolved image: {filename}')
