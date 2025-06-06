# gui.py

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from deconvolution import setup_imagej, process, save_image
import os
import threading

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
        default_wavelengths = [647, 594, 488, 405]
        default_wavelengths_str = ", ".join(str(w) for w in default_wavelengths)
        self.wavelengths_str = tk.StringVar(value=default_wavelengths_str)
        self.na = tk.DoubleVar(value=1.5)
        self.ri_immersion = tk.DoubleVar(value=1.0)
        self.ri_sample = tk.DoubleVar(value=1.0)
        self.lat_res = tk.DoubleVar(value=0.07)
        self.ax_res = tk.DoubleVar(value=1.0)
        self.pz = tk.DoubleVar(value=0.0)

        # Layout
        row = 0
        tk.Label(root, text="Folder containing TIFF's").grid(row=row, column=0)
        tk.Entry(root, textvariable=self.wd, width=40).grid(row=row, column=1)
        tk.Button(root, text="Browse", command=self.browse_dir).grid(row=0, column=2)
        row += 1
        tk.Label(root, text="TIFF File").grid(row=row, column=0)
        tk.Entry(root, textvariable=self.filename, width=40).grid(row=row, column=1)
        tk.Button(root, text="Select", command=self.select_file).grid(row=1, column=2)
        row += 1
        tk.Label(root, text="Iterations").grid(row=row, column=0)
        tk.Entry(root, textvariable=self.iterations).grid(row=row, column=1)
        row += 1
        tk.Label(root, text="Regularization").grid(row=row, column=0)
        tk.Entry(root, textvariable=self.reg).grid(row=row, column=1)
        row += 1
        tk.Label(root, text="Wavelengths(nm, comma-separated, in channel order)").grid(row=row, column=0)
        tk.Entry(root, textvariable=self.wavelengths_str).grid(row=row, column=1)
        row += 1
        tk.Label(root, text="Numerical Aperture (NA)").grid(row=row, column=0)
        tk.Entry(root, textvariable=self.na).grid(row=row, column=1)
        row += 1
        tk.Label(root, text="Refractive Index (Immersion)").grid(row=row, column=0)
        tk.Entry(root, textvariable=self.ri_immersion).grid(row=row, column=1)
        row += 1
        tk.Label(root, text="Refractive Index (Sample)").grid(row=row, column=0)
        tk.Entry(root, textvariable=self.ri_sample).grid(row=row, column=1)
        row += 1
        tk.Label(root, text="Lateral Resolution (um)").grid(row=row, column=0)
        tk.Entry(root, textvariable=self.lat_res).grid(row=row, column=1)
        row += 1
        tk.Label(root, text="Axial Resolution (um)").grid(row=row, column=0)
        tk.Entry(root, textvariable=self.ax_res).grid(row=row, column=1)
        row += 1
        tk.Label(root, text="PZ (um)").grid(row=row, column=0)
        tk.Entry(root, textvariable=self.pz).grid(row=row, column=1)
        row += 1
        # Run button
        tk.Button(root, text="Run Deconvolution", command=self.run).grid(row=row, column=0, columnspan=3, pady=10)


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

    def run_threaded(self):
        thread = threading.Thread(target=self.run)
        thread.start()

    def run(self):
        try:
            self.progress.start()

            wd = self.wd.get()
            img = self.filename.get()
            wavelength_str = self.wavelengths_str.get()
            wavelength = [int(w.strip()) for w in wavelength_str.split(',') if w.strip().isdigit()]
            iterations = self.iterations.get()
            reg = self.reg.get()
            iterstring = f"{iterations:02}"

            # Fixed parameters for now
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
            self.progress.stop()
            self.root.after(0, lambda e=e: messagebox.showerror("Error", str(e)))



# Run GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = DeconGUI(root)
    root.mainloop()
