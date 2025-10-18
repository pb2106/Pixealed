"""
Pixealed Image Viewer - Python Desktop Application
Secure viewer for encrypted .pxl files
Now supports .zip bundles containing .pxl and public key
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import io
import os
import zipfile
import tempfile
import shutil
import json

# Import from your pxl_converter modules
try:
    from modules.converter import read_pxl
except ImportError:
    def read_pxl(path, public_key_path=None):
        raise RuntimeError("read_pxl() not available — run from full Pixealed project context.")


class PxlViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Pixealed Image Viewer")
        self.root.geometry("1000x800")
        self.root.configure(bg="#1a1a2e")
        
        self.current_image = None
        self.current_metadata = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # Title
        title_frame = tk.Frame(self.root, bg="#1a1a2e")
        title_frame.pack(pady=20)
        
        title = tk.Label(
            title_frame,
            text="🔒 Pixealed Image Viewer",
            font=("Arial", 24, "bold"),
            fg="#bb86fc",
            bg="#1a1a2e"
        )
        title.pack()
        
        subtitle = tk.Label(
            title_frame,
            text="Decrypt and view .pxl or .zip (Pixealed bundle)",
            font=("Arial", 12),
            fg="#9d9d9d",
            bg="#1a1a2e"
        )
        subtitle.pack()
        
        # Upload Button
        self.upload_btn = tk.Button(
            self.root,
            text="📁 Open .pxl or .zip File",
            font=("Arial", 14, "bold"),
            bg="#bb86fc",
            fg="white",
            activebackground="#9d6fd4",
            activeforeground="white",
            padx=30,
            pady=15,
            cursor="hand2",
            command=self.open_file
        )
        self.upload_btn.pack(pady=20)
        
        # Image Display Frame
        self.image_frame = tk.Frame(self.root, bg="#0f0f1e", relief=tk.SUNKEN, bd=2)
        self.image_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        self.image_label = tk.Label(
            self.image_frame,
            text="No image loaded\n\nClick 'Open .pxl or .zip File' to decrypt and view an image",
            font=("Arial", 14),
            fg="#6d6d6d",
            bg="#0f0f1e"
        )
        self.image_label.pack(expand=True)
        
        # Metadata Frame
        self.metadata_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.metadata_frame.pack(pady=10, padx=20, fill=tk.X)
        
        self.metadata_text = tk.Text(
            self.metadata_frame,
            height=8,
            font=("Courier", 10),
            bg="#0f0f1e",
            fg="#bb86fc",
            insertbackground="#bb86fc",
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.metadata_text.pack(fill=tk.BOTH, expand=True)
        self.metadata_text.config(state=tk.DISABLED)
    
    def open_file(self):
        filepath = filedialog.askopenfilename(
            title="Select .pxl or .zip file",
            filetypes=[("Pixealed files", "*.pxl *.zip"), ("All files", "*.*")]
        )
        
        if filepath:
            ext = os.path.splitext(filepath)[1].lower()
            if ext == ".pxl":
                self.load_pxl_file(filepath)
            elif ext == ".zip":
                self.load_zip_bundle(filepath)
            else:
                messagebox.showwarning("Invalid File", "Please select a .pxl or .zip file.")
    
    def load_zip_bundle(self, zip_path):
        temp_dir = tempfile.mkdtemp()
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find .pxl and public key inside
            pxl_file = None
            pubkey_file = None
            for name in os.listdir(temp_dir):
                if name.endswith(".pxl"):
                    pxl_file = os.path.join(temp_dir, name)
                elif name.endswith(".pub") or "public" in name.lower():
                    pubkey_file = os.path.join(temp_dir, name)
            
            if not pxl_file:
                raise FileNotFoundError("No .pxl file found inside ZIP.")
            
            # Load the .pxl file (pass key path if available)
            self.load_pxl_file(pxl_file, pubkey_file)
        
        except zipfile.BadZipFile:
            messagebox.showerror("Invalid ZIP", "The selected ZIP file is corrupted or invalid.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open bundle:\n\n{str(e)}")
        finally:
            # Clean up temp folder after displaying
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def load_pxl_file(self, filepath, public_key_path=None):
        try:
            image_bytes, manifest = read_pxl(filepath)
            
            # Display image
            image = Image.open(io.BytesIO(image_bytes))
            self.display_image(image)
            
            # Display metadata
            self.display_metadata(manifest.get("metadata", {}))
            
            self.current_image = image
            self.current_metadata = manifest
            
        except Exception as e:
            messagebox.showerror(
                "Decryption Error",
                f"Failed to decrypt .pxl file:\n\n{str(e)}"
            )
    
    def display_image(self, image):
        display_width = 900
        display_height = 500
        
        img_width, img_height = image.size
        ratio = min(display_width/img_width, display_height/img_height)
        
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(resized_image)
        
        self.image_label.config(image=photo, text="")
        self.image_label.image = photo
    
    def display_metadata(self, metadata):
        self.metadata_text.config(state=tk.NORMAL)
        self.metadata_text.delete(1.0, tk.END)
        
        if metadata:
            self.metadata_text.insert(tk.END, "📷 Image Metadata:\n\n")
            for key, value in metadata.items():
                self.metadata_text.insert(tk.END, f"{key:20s}: {value}\n")
        else:
            self.metadata_text.insert(tk.END, "No metadata available")
        
        self.metadata_text.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = PxlViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
