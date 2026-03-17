# AM-Flow Batch Maker

The **AM-Flow Batch Maker** is an internal desktop tool designed to streamline the preparation of STL files for AM-Flow systems. 

It takes a ZIP file containing your 3D models (STLs), sanitizes the filenames, generates random order IDs, and automatically builds the required `meta.csv` file. It also safely splits large batches into smaller folders of 100 files each, ready for upload.

## 📥 How to Download

### Windows Installation

You do not need to install Python or any special software to run this tool. 

1. On this GitHub page, look at the right side of the screen for the **Releases** section.
2. Click on the latest release. 
3. Under the **Assets** dropdown at the bottom of the release notes, click on **`Batch_Maker.exe`** to download it.
4. Once downloaded, you can move the `.exe` file to your Desktop or anywhere convenient. Just double-click it to run!

*(Note: If Windows SmartScreen shows a "Windows protected your PC" popup, click **More info** -> **Run anyway**. This happens because the app is an internal tool and not signed by a commercial publisher.)*

### Linux Installation

1. Create a folder in a convinient location on your computer
2. Download and place app.py in that folder
3. Open terminal in that same folder and update your packages. On a Debian based distro such as Ubuntu, use `sudo apt update`
4. Install python3 and its dependencies. `sudo apt install python3 python3-pip python3-tk` (If you already have the latest versions of PIP and Python installed, just install `python3-tk`)
5. Install PyInstaller. `pip3 install pyinstaller`
6. Build the app. `pyinstaller --noconsole --onefile app.py`

*(Note: Before running it for the first time you may need to update the permissions for this app to run. Do so by running this command in terminal: `chmod +x AMFlow_Batch_Creator_Linux`)*

## 🚀 How to Use

### 1. Prepare Your Files
Place all the `.stl` files you want to process into a single `.zip` file. (Select the files, right-click -> Compress to ZIP file). 

### 2. Run the Tool
Double-click `Batch_Maker.exe` to open the application.

### 3. Fill Out the Batch Details
* **Browse ZIP:** Click this button and select the ZIP file you created in Step 1.
* **Batch Name:** Enter the name of the batch (this will be applied to all files).
* **Material:** Enter the material type (e.g., PA12).
* **Technology:** Enter the print technology (e.g., MJF, SLS).

### 4. Advanced Editing (Optional)
If you need specific files to have different properties (like a different material, more than 1 copy, or a different technology), click the **Advanced (Edit CSV)** button.
* A spreadsheet-like view will open.
* Click on any row to select it, change the values at the bottom, and click **Update Selected Row**.

### 5. Start Processing
Click the green **Start Processing** button. 

### 6. Uploading the Batch
* Open the admin page of the machine you want to upload batches to, and navigate to `Batches`.
* Click on **Upload Zip File** to open the upload tool.
* Click on **browse...** to open file explorer.
* Select the ZIP file of the batch you want to upload and click **Upload Zip File** to upload the batch.

## 📂 Output & Automated Rules

Once processing is complete, a new folder will automatically appear on your **Desktop** named `Batch_[YourBatchName]`. 

Inside, you will find your files formatted perfectly for AM-Flow:
* **`meta.csv` Generation:** A properly formatted CSV file (UTF-8) is generated automatically alongside your files.
* **Filename Cleaning:** Any unsupported characters in your original STL filenames will be automatically replaced with underscores (`_`) or dashes (`-`) to meet the strict `a-z`, `0-9`, `-`, `_`, `()`, `,` spec.
* **Auto-Splitting:** If your ZIP contains more than 100 STLs, the tool will automatically divide them into sub-folders (`step_1`, `step_2`, etc.), each with a maximum of 100 STLs and its own `meta.csv`.
* **Randomized Order IDs:** Every file is assigned a unique, random order ID.
