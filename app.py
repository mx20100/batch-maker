import os
import json
import zipfile
import csv
import random
import re
import tempfile
import io
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

KEYRING_SERVICE = "AMFlowBatchCreator"
KEYRING_USERNAME = "api_token"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "AMFlowBatchCreator")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


def fetch_all_materials(ip, token):
    """Fetch all material IDs from the machine API, following pagination."""
    headers = {"Authorization": f"Token {token}"} if token else {}
    url = f"http://{ip}/api/material/"
    materials = []
    while url:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("results", []):
            mat_id = item.get("id")
            if mat_id is not None:
                materials.append(str(mat_id))
        url = data.get("next")
    return sorted(materials, key=str.lower)


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Machine Settings")
        self.resizable(False, False)
        self.grab_set()

        config = load_config()

        tk.Label(self, text="Machine Connection", font=("Arial", 11, "bold")).pack(pady=(15, 5))

        warnings = []
        if not REQUESTS_AVAILABLE:
            warnings.append("'requests' library not installed.\nRun: pip install requests")
        if not KEYRING_AVAILABLE:
            warnings.append("'keyring' library not installed.\nToken will not be stored securely.\nRun: pip install keyring")
        for w in warnings:
            tk.Label(self, text=w, fg="orange", justify="left").pack(padx=20, pady=2, anchor="w")

        form = tk.Frame(self)
        form.pack(padx=20, pady=8)

        tk.Label(form, text="IP Address:").grid(row=0, column=0, sticky="e", pady=6, padx=5)
        self.entry_ip = tk.Entry(form, width=28)
        self.entry_ip.grid(row=0, column=1, pady=6)
        self.entry_ip.insert(0, config.get("machine_ip", ""))

        tk.Label(form, text="Auth Token:").grid(row=1, column=0, sticky="e", pady=6, padx=5)
        self.entry_token = tk.Entry(form, width=28, show="*")
        self.entry_token.grid(row=1, column=1, pady=6)
        if KEYRING_AVAILABLE:
            stored = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME) or ""
            self.entry_token.insert(0, stored)

        self.lbl_status = tk.Label(self, text="", fg="gray")
        self.lbl_status.pack(pady=4)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Test Connection", command=self.test_connection).grid(row=0, column=0, padx=6)
        tk.Button(btn_frame, text="Save", bg="green", fg="white", command=self.save).grid(row=0, column=1, padx=6)
        tk.Button(btn_frame, text="Cancel", command=self.destroy).grid(row=0, column=2, padx=6)

        self.update_idletasks()
        self.geometry("")

    def test_connection(self):
        ip = self.entry_ip.get().strip()
        token = self.entry_token.get().strip()
        if not ip:
            self.lbl_status.config(text="Please enter an IP address.", fg="red")
            return
        if not REQUESTS_AVAILABLE:
            self.lbl_status.config(text="'requests' library not installed.", fg="red")
            return
        self.lbl_status.config(text="Testing...", fg="gray")
        self.update()
        try:
            headers = {"Authorization": f"Token {token}"} if token else {}
            resp = requests.get(f"http://{ip}/api/material/", headers=headers, timeout=5)
            if resp.status_code == 200:
                count = resp.json().get("count", "?")
                self.lbl_status.config(text=f"Connected! {count} materials found.", fg="green")
            else:
                self.lbl_status.config(text=f"HTTP {resp.status_code}: connection failed.", fg="red")
        except Exception as e:
            self.lbl_status.config(text=f"Error: {e}", fg="red")

    def save(self):
        ip = self.entry_ip.get().strip()
        token = self.entry_token.get().strip()
        config = load_config()
        config["machine_ip"] = ip
        save_config(config)
        if KEYRING_AVAILABLE:
            if token:
                keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, token)
            else:
                try:
                    keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
                except Exception:
                    pass
        self.destroy()
        self.parent.try_connect()


class AMFlowBatchCreator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AM-Flow Batch Creator")
        self.geometry("520x470")

        self.zip_filepath = ""
        self.file_data = []
        self.available_materials = []

        # --- Top bar ---
        top_bar = tk.Frame(self)
        top_bar.pack(fill="x", padx=10, pady=(8, 0))

        self.lbl_connection = tk.Label(top_bar, text="Not connected", fg="gray", font=("Arial", 9))
        self.lbl_connection.pack(side="left")

        tk.Button(top_bar, text="Settings", command=self.open_settings).pack(side="right")

        # --- File selection ---
        tk.Label(self, text="1. Select ZIP File containing STLs", font=("Arial", 10, "bold")).pack(pady=(12, 5))

        self.btn_select = tk.Button(self, text="Browse ZIP", command=self.select_zip)
        self.btn_select.pack()

        self.lbl_file = tk.Label(self, text="No file selected", fg="gray")
        self.lbl_file.pack(pady=(0, 10))

        # --- Batch info ---
        tk.Label(self, text="2. Batch Information", font=("Arial", 10, "bold")).pack(pady=(10, 5))

        form_frame = tk.Frame(self)
        form_frame.pack()

        tk.Label(form_frame, text="Batch Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_batch = tk.Entry(form_frame, width=25)
        self.entry_batch.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Material:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.combo_material = ttk.Combobox(form_frame, width=23, values=[])
        self.combo_material.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Technology:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.entry_technology = tk.Entry(form_frame, width=25)
        self.entry_technology.grid(row=2, column=1, padx=5, pady=5)

        # --- Action buttons ---
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)

        self.btn_advanced = tk.Button(btn_frame, text="Advanced (Edit CSV)", command=self.open_advanced)
        self.btn_advanced.grid(row=0, column=0, padx=10)

        self.btn_start = tk.Button(
            btn_frame, text="Start Processing",
            bg="green", fg="white", font=("Arial", 10, "bold"),
            command=self.process_batch
        )
        self.btn_start.grid(row=0, column=1, padx=10)

        self.after(200, self.try_connect)

    def open_settings(self):
        SettingsDialog(self)

    def try_connect(self):
        if not REQUESTS_AVAILABLE:
            return
        config = load_config()
        ip = config.get("machine_ip", "").strip()
        if not ip:
            return
        token = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME) or "" if KEYRING_AVAILABLE else ""
        self.lbl_connection.config(text="Connecting...", fg="orange")

        def fetch():
            try:
                materials = fetch_all_materials(ip, token)
                self.after(0, lambda: self._on_connected(ip, materials))
            except Exception:
                self.after(0, self._on_connect_failed)

        threading.Thread(target=fetch, daemon=True).start()

    def _on_connected(self, ip, materials):
        self.available_materials = materials
        self.lbl_connection.config(text=f"Connected: {ip}  ({len(materials)} materials)", fg="green")
        self.combo_material["values"] = materials

    def _on_connect_failed(self):
        self.available_materials = []
        self.lbl_connection.config(text="Not connected", fg="gray")
        self.combo_material["values"] = []

    def select_zip(self):
        filepath = filedialog.askopenfilename(filetypes=[("ZIP Files", "*.zip")])
        if filepath:
            self.zip_filepath = filepath
            self.lbl_file.config(text=os.path.basename(filepath), fg="black")
            self.file_data = []

    def sanitize_filename(self, filename):
        name, ext = os.path.splitext(filename)
        clean_name = re.sub(r'[^a-z0-9\-_\(\)]', '_', name.lower())
        return f"{clean_name}.stl", clean_name

    def generate_base_data(self):
        if not self.zip_filepath:
            messagebox.showerror("Error", "Please select a ZIP file first.")
            return False

        if self.file_data:
            return True

        batch = self.entry_batch.get().strip()
        material = self.combo_material.get().strip()
        technology = self.entry_technology.get().strip()

        if not all([batch, material, technology]):
            messagebox.showerror("Error", "Please fill in Batch, Material, and Technology.")
            return False

        try:
            with zipfile.ZipFile(self.zip_filepath, 'r') as z:
                stl_files = [
                    f for f in z.namelist()
                    if f.lower().endswith('.stl') and not f.startswith('__MACOSX')
                ]

            if not stl_files:
                messagebox.showerror("Error", "No STL files found in the ZIP.")
                return False

            max_id = max(1000, len(stl_files) * 2)
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
                    "technology": technology,
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
        adv_window.geometry("980x470")

        columns = ("batch", "filename", "material", "part_id", "copies", "next_step", "order_id", "technology")
        tree = ttk.Treeview(adv_window, columns=columns, show="headings")

        col_widths = {
            "batch": 90, "filename": 190, "material": 90, "part_id": 130,
            "copies": 55, "next_step": 80, "order_id": 70, "technology": 90,
        }
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=col_widths.get(col, 100))

        for idx, row in enumerate(self.file_data):
            tree.insert("", "end", iid=idx, values=tuple(row[c] for c in columns))

        tree.pack(fill="both", expand=True)

        edit_frame = tk.Frame(adv_window)
        edit_frame.pack(pady=8)

        tk.Label(
            edit_frame, text="Select a row, edit fields below, then click Update.",
            font=("Arial", 9)
        ).grid(row=0, column=0, columnspan=8, pady=(0, 6))

        edit_vars = {col: tk.StringVar() for col in columns}

        # Editable columns and their widget types
        editable = [("material", "combobox"), ("part_id", "entry"), ("copies", "entry"), ("technology", "entry")]

        c = 0
        for col, kind in editable:
            label = col.replace("_", " ").capitalize()
            tk.Label(edit_frame, text=f"{label}:").grid(row=1, column=c, padx=5, sticky="e")
            if kind == "combobox":
                w = ttk.Combobox(edit_frame, textvariable=edit_vars[col], width=16, values=self.available_materials)
            else:
                w = tk.Entry(edit_frame, textvariable=edit_vars[col], width=18)
            w.grid(row=1, column=c + 1, padx=5)
            c += 2

        def on_select(_event):
            selected = tree.selection()
            if selected:
                item = tree.item(selected[0])["values"]
                for i, col in enumerate(columns):
                    edit_vars[col].set(item[i])

        tree.bind("<<TreeviewSelect>>", on_select)

        def update_row():
            selected = tree.selection()
            if not selected:
                return
            idx = int(selected[0])
            for col, _ in editable:
                self.file_data[idx][col] = edit_vars[col].get()
            tree.item(selected[0], values=tuple(self.file_data[idx][c] for c in columns))

        tk.Button(edit_frame, text="Update Selected Row", command=update_row).grid(
            row=2, column=0, columnspan=8, pady=8
        )

    def process_batch(self):
        if not self.generate_base_data():
            return

        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            batch_name = self.entry_batch.get().strip()
            output_folder = os.path.join(desktop_path, f"Batch_{batch_name}")

            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(self.zip_filepath, 'r') as z:
                    z.extractall(temp_dir)

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

                for step_idx, chunk in enumerate(chunks):
                    zip_filename = (
                        f"{batch_name}_part{step_idx + 1}.zip" if len(chunks) > 1 else f"{batch_name}.zip"
                    )
                    zip_filepath = os.path.join(output_folder, zip_filename)

                    with zipfile.ZipFile(zip_filepath, 'w', compression=zipfile.ZIP_STORED) as out_zip:
                        csv_buffer = io.StringIO()
                        writer = csv.writer(csv_buffer)
                        writer.writerow(["batch", "filename", "material", "part_id", "copies", "next_step", "order_id", "technology"])

                        for row in chunk:
                            writer.writerow([
                                row["batch"], row["filename"], row["material"],
                                row["part_id"], row["copies"], row["next_step"],
                                row["order_id"], row["technology"],
                            ])

                        out_zip.writestr("meta.csv", csv_buffer.getvalue().encode("utf-8"))

                        for row in chunk:
                            src_path = os.path.join(temp_dir, row["original_path"])
                            out_zip.write(src_path, arcname=row["filename"])

            messagebox.showinfo(
                "Success",
                f"Batch processed successfully!\nSaved to Desktop: {os.path.basename(output_folder)}\n"
                f"Total ZIP archives created: {len(chunks)}"
            )
            self.file_data = []
            self.lbl_file.config(text="No file selected", fg="gray")
            self.zip_filepath = ""

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during processing:\n{e}")


if __name__ == "__main__":
    app = AMFlowBatchCreator()
    app.mainloop()
