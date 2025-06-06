# gui.py

import tkinter as tk
from tkinter import filedialog, messagebox
from deconvolution import setup_imagej, process, save_image
import os

class DeconGUI:
    def __init__(self, root):
        self.root = root
        root.title("3D Deconvolution Tool")

        self.ij = setup_imagej()

        # Variables
        self.wd = tk.StringVar()
        self.filename = tk.StringVar()
        self.iterations = tk.IntVar(value=1)
        self.reg = tk.DoubleVar(value=0.002)

        # Layout
        tk.Label(root, text="Working Directory").grid(row=0, column=0)
        tk.Entry(root, textvariable=self.wd, width=40).grid(row=0, column=1)
        tk.Button(root, text="Browse", command=self.browse_dir).grid(row=0, column=2)

        tk.Label(root, text="TIFF File").grid(row=1, column=0)
        tk.Entry(root, textvariable=self.filename, width=40).grid(row=1, column=1)
        tk.Button(root, text="Select", command=self.select_file).grid(row=1, column=2)

        tk.Label(root, text="Iterations").grid(row=2, column=0)
        tk.Entry(root, textvariable=self.iterations).grid(row=2, column=1)

        tk.Label(root, text="Regularization").grid(row=3, column=0)
        tk.Entry(root, textvariable=self.reg).grid(row=3, column=1)

        tk.Button(root, text="Run Deconvolution", command=self.run).grid(row=4, column=0, columnspan=3, pady=10)

    def browse_dir(self):
        dir_selected = filedialog.askdirectory()
        if dir_selected:
            self.wd.set(dir_selected)

    def select_file(self):
        file_selected = filedialog.askopenfilename(
            initialdir=self.wd.get(),
            filetypes=[("TIFF files", "*.tif")])
        if file_selected:
            self.filename.set(os.path.basename(file_selected))

    def run(self):
        try:
            wd = self.wd.get()
            img = self.filename.get()
            iterations = self.iterations.get()
            reg = self.reg.get()
            iterstring = f"{iterations:02}"

            # Fixed parameters for now
            wavelength = [647, 594, 488, 405]
            na = 1.5
            ri_immersion = 1.0
            ri_sample = 1.0
            lat_res = 0.07
            ax_res = 1.0
            pz = 0.0

            img_path = os.path.join(wd, img)
            decon_img = process(
                self.ij, img_path, wavelength, iterations, reg,
                na, ri_sample, ri_immersion, lat_res, ax_res, pz
            )
            save_image(self.ij, wd, img, decon_img, iterstring, reg)
            messagebox.showinfo("Success", "Deconvolution complete!")

        except Exception as e:
            messagebox.showerror("Error", str(e))

# Run GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = DeconGUI(root)
    root.mainloop()
