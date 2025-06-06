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
        self.channel = tk.StringVar(value="All")
        self.process_all = tk.BooleanVar()

        self.wavelengths = {
            "405 nm": 405,
            "488 nm": 488,
            "594 nm": 594,
            "647 nm": 647,
            "All": "All"
        }

        # Layout
        tk.Label(root, text="Working Directory").grid(row=0, column=0)
        tk.Entry(root, textvariable=self.wd, width=40).grid(row=0, column=1)
        tk.Button(root, text="Browse", command=self.browse_dir).grid(row=0, column=2)

        tk.Label(root, text="TIFF File").grid(row=1, column=0)
        tk.Entry(root, textvariable=self.filename, width=40).grid(row=1, column=1)
        tk.Button(root, text="Select", command=self.select_file).grid(row=1, column=2)

        tk.Checkbutton(root, text="Process All .tif Files", variable=self.process_all).grid(row=2, column=0, columnspan=2, sticky="w")

        tk.Label(root, text="Channel").grid(row=3, column=0)
        tk.OptionMenu(root, self.channel, *self.wavelengths.keys()).grid(row=3, column=1, sticky="ew")

        tk.Label(root, text="Iterations").grid(row=4, column=0)
        tk.Entry(root, textvariable=self.iterations).grid(row=4, column=1)

        tk.Label(root, text="Regularization").grid(row=5, column=0)
        tk.Entry(root, textvariable=self.reg).grid(row=5, column=1)

        self.progress = ttk.Progressbar(root, mode="indeterminate")
        self.progress.grid(row=6, column=0, columnspan=3, pady=10, sticky="ew")

        tk.Button(root, text="Run Deconvolution", command=self.run_threaded).grid(row=7, column=0, columnspan=3, pady=10)

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
            iterations = self.iterations.get()
            reg = self.reg.get()
            iterstring = f"{iterations:02}"
            channel_label = self.channel.get()
            selected_wavelength = self.wavelengths[channel_label]

            if self.process_all.get():
                files = [f for f in os.listdir(wd) if f.lower().endswith('.tif')]
            else:
                files = [self.filename.get()]

            for img in files:
                img_path = os.path.join(wd, img)
                decon_img = process(
                    self.ij, img_path,
                    wavelength=selected_wavelength if selected_wavelength != "All" else [647, 594, 488, 405],
                    iterations=iterations, reg=reg,
                    na=1.5, ri_sample=1.0, ri_immersion=1.0,
                    lat_res=0.07, ax_res=1.0, pz=0.0
                )
                save_image(self.ij, wd, img, decon_img, iterstring, reg)

            self.progress.stop()
            self.root.after(0, lambda: messagebox.showinfo("Success", "Deconvolution complete."))


        except Exception as e:
            self.progress.stop()
            self.root.after(0, lambda e=e: messagebox.showerror("Error", str(e)))



# Run GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = DeconGUI(root)
    root.mainloop()
