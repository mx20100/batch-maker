# AM-Flow Batch Maker

The **AM-Flow Batch Maker** is an internal desktop tool designed to streamline the preparation of STL files for AM-Flow systems.

It takes a ZIP file containing your 3D models (STLs), sanitizes the filenames, generates random order IDs, and automatically builds the required `meta.csv` file. It also safely splits large batches when they exceed 900 MB, ready for upload.

## 📥 How to Download

### Windows Installation

You do not need to install Python or any special software to run this tool.

1. On this GitHub page, look at the right side of the screen for the **Releases** section.
2. Click on the latest release.
3. Under the **Assets** dropdown at the bottom of the release notes, click on **`Batch_Maker.exe`** to download it.
4. Once downloaded, you can move the `.exe` file to your Desktop or anywhere convenient. Just double-click it to run!

*(Note: If Windows SmartScreen shows a "Windows protected your PC" popup, click **More info** → **Run anyway**. This happens because the app is an internal tool and not signed by a commercial publisher.)*

### Linux Installation

1. Create a folder in a convenient location on your computer.
2. Download and place `app.py` in that folder.
3. Open a terminal in that folder and update your packages. On a Debian-based distro such as Ubuntu: `sudo apt update`
4. Install Python 3 and its dependencies: `sudo apt install python3 python3-pip python3-tk`
5. Install the required libraries: `pip3 install pyinstaller requests keyring`
6. Build the app: `pyinstaller --noconsole --onefile app.py`

*(Note: Before running it for the first time you may need to update permissions: `chmod +x dist/batch_maker`)*

## ⚙️ Machine Connection (Optional)

The tool can connect to your AM-Flow machine to automatically fetch the list of available materials.

### Setting Up the Connection

1. Click the **Settings** button in the top-right corner of the app.
2. Enter the **IP address** of your machine (e.g. `192.168.0.120`).
3. Enter your **Auth Token**.
4. Click **Test Connection** to verify — it will confirm how many materials were found.
5. Click **Save**.

The auth token is stored securely in the **Windows Credential Manager** (encrypted at OS level). The IP address is saved to `%AppData%\Local\AMFlowBatchCreator\config.json`.

### Connection Status

The top-left of the app shows the current connection state:
* **Not connected** — no machine configured, or the machine is unreachable. Material must be entered manually.
* **Connecting...** — fetching materials in the background at startup.
* **Connected: 192.168.x.x (N materials)** — successfully connected; the material dropdown is populated.

## 🚀 How to Use

### 1. Prepare Your Files
Place all the `.stl` files you want to process into a single `.zip` file (select the files, right-click → Compress to ZIP file).

### 2. Run the Tool
Double-click `Batch_Maker.exe` to open the application.

### 3. Fill Out the Batch Details
* **Browse ZIP:** Click this button and select the ZIP file you created in Step 1.
* **Batch Name:** Enter the name of the batch (applied to all files).
* **Material:** Select a material from the dropdown (populated from the machine when connected), or type a new material name directly.
* **Technology:** Enter the print technology (e.g., MJF, SLS).

### 4. Advanced Editing (Optional)
If you need specific files to have different properties, click the **Advanced (Edit CSV)** button.
* A spreadsheet-like view will open showing all files in the batch.
* Click any row to select it, edit the fields at the bottom, and click **Update Selected Row**.
* The following fields are editable per row:
  * **Material** — dropdown (same machine materials) or free-text entry.
  * **Part ID** — custom identifier for the part (defaults to the sanitized filename).
  * **Copies** — how many copies to produce.
  * **Technology** — print technology for that specific file.

### 5. Start Processing
Click the green **Start Processing** button.

### 6. Uploading the Batch
* Open the admin page of the machine and navigate to **Batches**.
* Click **Upload Zip File** to open the upload tool.
* Click **browse...**, select the ZIP file, and click **Upload Zip File**.

## 📂 Output & Automated Rules

Once processing is complete, a new folder appears on your **Desktop** named `Batch_[YourBatchName]`.

Inside, you will find your files formatted for AM-Flow:
* **`meta.csv` Generation:** A properly formatted CSV file (UTF-8) is generated automatically alongside your STL files.
* **Filename Cleaning:** Unsupported characters in original filenames are replaced with underscores (`_`) to meet the `a-z`, `0-9`, `-`, `_`, `()` spec.
* **Auto-Splitting:** If your total batch exceeds 900 MB, the tool automatically splits it into multiple ZIP archives (`batch_part1.zip`, `batch_part2.zip`, etc.), each with its own `meta.csv`.
* **Randomized Order IDs:** Every file is assigned a unique, random order ID.
