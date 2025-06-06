from deconvolution import setup_imagej, process, save_image
import os

# ---- SET PARAMETERS ----
iterations = 1
reg = 0.002
na = 1.5
wavelength = [647, 594, 488, 405]
ri_immersion = 1.0
ri_sample = 1.0
lat_res = 0.07
ax_res = 1.0
pz = 0.0

# ---- START SCRIPT ----
ij = setup_imagej()

# Get working directory and image name from user
wd = input("Enter the directory with images:\n").strip()
img_list = [f for f in os.listdir(wd) if f.lower().endswith('.tif')]
print("\n.tif files found:")
for img in img_list:
    print(f" - {img}")
img = input("\nEnter the filename to deconvolve:\n").strip()

# Run processing
img_path = os.path.join(wd, img)
decon_img = process(
    ij, img_path, wavelength, iterations, reg, na,
    ri_sample, ri_immersion, lat_res, ax_res, pz
)
iterstring = f"{iterations:02}"
save_image(ij, wd, img, decon_img, iterstring, reg)

ij.dispose()
