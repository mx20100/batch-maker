import os
import zipfile
import shutil
import csv
import random
import re
import tempfile
import io
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class AMFlowBatchCreator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AM-Flow Batch Creator")
        self.geometry("500x400")
        
        self.zip_filepath = ""
        self.file_data = [] # Stores file row data in memory
        
        # GUI Elements
        tk.Label(self, text="1. Select ZIP File containing STLs", font=("Arial", 10, "bold")).pack(pady=(15, 5))
        
        self.btn_select = tk.Button(self, text="Browse ZIP", command=self.select_zip)
        self.btn_select.pack()
        
        self.lbl_file = tk.Label(self, text="No file selected", fg="gray")
        self.lbl_file.pack(pady=(0, 10))
        
        tk.Label(self, text="2. Batch Information", font=("Arial", 10, "bold")).pack(pady=(10, 5))
        
        form_frame = tk.Frame(self)
        form_frame.pack()
        
        tk.Label(form_frame, text="Batch Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_batch = tk.Entry(form_frame, width=25)
        self.entry_batch.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="Material:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entry_material = tk.Entry(form_frame, width=25)
        self.entry_material.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="Technology:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.entry_technology = tk.Entry(form_frame, width=25)
        self.entry_technology.grid(row=2, column=1, padx=5, pady=5)

        # Buttons Frame
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)

        self.btn_advanced = tk.Button(btn_frame, text="Advanced (Edit CSV)", command=self.open_advanced)
        self.btn_advanced.grid(row=0, column=0, padx=10)
        
        self.btn_start = tk.Button(btn_frame, text="Start Processing", bg="green", fg="white", font=("Arial", 10, "bold"), command=self.process_batch)
        self.btn_start.grid(row=0, column=1, padx=10)

    def select_zip(self):
        filepath = filedialog.askopenfilename(filetypes=[("ZIP Files", "*.zip")])
        if filepath:
            self.zip_filepath = filepath
            self.lbl_file.config(text=os.path.basename(filepath), fg="black")
            self.file_data = [] # Reset data if new zip is selected

    def sanitize_filename(self, filename):
        # Separate name and extension
        name, ext = os.path.splitext(filename)
        # Convert to lowercase and replace non-compliant characters with an underscore
        # Compliant: a-z, 0-9, -, _, (, )
        clean_name = re.sub(r'[^a-z0-9\-_\(\)]', '_', name.lower())
        return f"{clean_name}.stl", clean_name

    def generate_base_data(self):
        """Reads the ZIP and generates base memory data if not done yet."""
        if not self.zip_filepath:
            messagebox.showerror("Error", "Please select a ZIP file first.")
            return False
            
        if self.file_data: 
            return True # Already generated/edited

        batch = self.entry_batch.get().strip()
        material = self.entry_material.get().strip()
        technology = self.entry_technology.get().strip()

        if not all([batch, material, technology]):
            messagebox.showerror("Error", "Please fill in Batch, Material, and Technology.")
            return False

        try:
            with zipfile.ZipFile(self.zip_filepath, 'r') as z:
                stl_files = [f for f in z.namelist() if f.lower().endswith('.stl') and not f.startswith('__MACOSX')]
                
            if not stl_files:
                messagebox.showerror("Error", "No STL files found in the ZIP.")
                return False

            # Generate unique random order IDs
            max_id = max(1000, len(stl_files) * 2) # Ensure we have enough pool if > 1000 files
            order_ids = random.sample(range(1, max_id + 1), len(stl_files))

            for i, original_path in enumerate(stl_files):
                original_filename = os.path.basename(original_path)
                clean_filename, part_id = self.sanitize_filename(original_filename)
                
                self.file_data.append({
                    "original_path": original_path,
                    "batch": batch,
                    "filename": clean_filename,
                    "material": material,
                    "part_id": part_id,
                    "copies": "1",
                    "next_step": "shipping",
                    "order_id": str(order_ids[i]),
                    "technology": technology
                })
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read ZIP: {e}")
            return False

    def open_advanced(self):
        if not self.generate_base_data():
            return
            
        adv_window = tk.Toplevel(self)
        adv_window.title("Advanced Row Editor")
        adv_window.geometry("900x400")
        
        columns = ("batch", "filename", "material", "part_id", "copies", "next_step", "order_id", "technology")
        tree = ttk.Treeview(adv_window, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
            
        for idx, row in enumerate(self.file_data):
            tree.insert("", "end", iid=idx, values=(row["batch"], row["filename"], row["material"], row["part_id"], row["copies"], row["next_step"], row["order_id"], row["technology"]))
            
        tree.pack(fill="both", expand=True)
        
        # Frame for editing selected row
        edit_frame = tk.Frame(adv_window)
        edit_frame.pack(pady=10)
        
        tk.Label(edit_frame, text="Select a row, edit properties, and update.").grid(row=0, column=0, columnspan=4)
        
        edit_vars = {col: tk.StringVar() for col in columns}
        
        def on_select(event):
            selected = tree.selection()
            if selected:
                item = tree.item(selected[0])['values']
                for i, col in enumerate(columns):
                    edit_vars[col].set(item[i])
                    
        tree.bind("<<TreeviewSelect>>", on_select)
        
        c = 0
        for col in ["material", "copies", "technology"]:
            tk.Label(edit_frame, text=f"{col.capitalize()}:").grid(row=1, column=c, padx=5)
            tk.Entry(edit_frame, textvariable=edit_vars[col], width=15).grid(row=1, column=c+1, padx=5)
            c += 2
            
        def update_row():
            selected = tree.selection()
            if selected:
                idx = int(selected[0])
                for col in columns:
                    if col in ["material", "copies", "technology"]:
                        self.file_data[idx][col] = edit_vars[col].get()
                
                # Update Treeview
                tree.item(selected[0], values=tuple(self.file_data[idx][col] for col in columns))
                
        tk.Button(edit_frame, text="Update Selected Row", command=update_row).grid(row=2, column=0, columnspan=4, pady=10)

    def process_batch(self):
        if not self.generate_base_data():
            return
            
        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            batch_name = self.entry_batch.get().strip()
            output_folder = os.path.join(desktop_path, f"Batch_{batch_name}")
            
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            # Extract zip to a temporary folder
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(self.zip_filepath, 'r') as z:
                    z.extractall(temp_dir)
                
                # Split logic (900 MB limit)
                max_size_bytes = 900 * 1024 * 1024
                chunks = []
                current_chunk = []
                current_size = 0
                
                for row in self.file_data:
                    file_path = os.path.join(temp_dir, row["original_path"])
                    file_size = os.path.getsize(file_path)
                    
                    if current_size + file_size > max_size_bytes and current_chunk:
                        chunks.append(current_chunk)
                        current_chunk = []
                        current_size = 0
                        
                    current_chunk.append(row)
                    current_size += file_size
                    
                if current_chunk:
                    chunks.append(current_chunk)
                
                # --- ZIP CREATION LOGIC ---
                for step_idx, chunk in enumerate(chunks):
                    # Name the zip file based on whether there's one or multiple chunks
                    if len(chunks) > 1:
                        zip_filename = f"{batch_name}_part{step_idx + 1}.zip"
                    else:
                        zip_filename = f"{batch_name}.zip"
                        
                    zip_filepath = os.path.join(output_folder, zip_filename)
                    
                    # Open a new ZIP file using ZIP_STORED for faster, uncompressed packaging
                    with zipfile.ZipFile(zip_filepath, 'w', compression=zipfile.ZIP_STORED) as out_zip:
                        
                        # Generate CSV in memory (RAM) instead of writing to disk
                        csv_buffer = io.StringIO()
                        writer = csv.writer(csv_buffer)
                        writer.writerow(["batch", "filename", "material", "part_id", "copies", "next_step", "order_id", "technology"])
                        
                        for row in chunk:
                            writer.writerow([
                                row["batch"], row["filename"], row["material"], 
                                row["part_id"], row["copies"], row["next_step"], 
                                row["order_id"], row["technology"]
                            ])
                            
                        # Write the memory CSV directly into the root of the ZIP file
                        out_zip.writestr("meta.csv", csv_buffer.getvalue().encode('utf-8'))
                        
                        # Write the STLs directly from the temp folder into the root of the ZIP file
                        for row in chunk:
                            src_path = os.path.join(temp_dir, row["original_path"])
                            out_zip.write(src_path, arcname=row["filename"])
                        
            messagebox.showinfo("Success", f"Batch processed successfully!\nSaved to Desktop: {os.path.basename(output_folder)}\nTotal ZIP archives created: {len(chunks)}")
            self.file_data = [] # Clear memory
            self.lbl_file.config(text="No file selected", fg="gray")
            self.zip_filepath = ""
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during processing:\n{e}")

if __name__ == "__main__":
    app = AMFlowBatchCreator()
    app.mainloop()