"""
Pixealed Image Viewer - Python Desktop Application
Secure viewer for encrypted .pxl files with tamper verification
Extracts zip files and uses embedded public key for verification
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import io
import os
import zipfile
import tempfile
import shutil

# Import from your pxl_converter modules
try:
    from modules.converter import read_pxl, verify_pxl
except ImportError:
    print("Error: pxl_converter module not found!")
    exit(1)


class PxlViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Pixealed Image Viewer")
        self.root.geometry("1000x800")
        self.root.configure(bg="#1a1a2e")
        
        self.current_image = None
        self.current_metadata = None
        self.temp_dir = None
        
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
            text="Tamper-proof verification & decryption",
            font=("Arial", 12),
            fg="#9d9d9d",
            bg="#1a1a2e"
        )
        subtitle.pack()
        
        # Status indicator
        self.status_label = tk.Label(
            self.root,
            text="Ready to load file",
            font=("Arial", 10),
            fg="#9d9d9d",
            bg="#1a1a2e"
        )
        self.status_label.pack()
        
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
    
    def cleanup_temp_dir(self):
        """Clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
            except Exception as e:
                print(f"Warning: Could not clean up temp directory: {e}")
    
    def extract_zip(self, zip_path):
        """Extract zip file and return paths to .pxl and public_key.bin"""
        self.cleanup_temp_dir()
        
        self.temp_dir = tempfile.mkdtemp(prefix="pxl_viewer_")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            
            # Find .pxl file and public_key.bin
            pxl_file = None
            public_key_file = None
            
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    if file.endswith('.pxl'):
                        pxl_file = os.path.join(root, file)
                    elif file == 'public_key.bin':
                        public_key_file = os.path.join(root, file)
            
            if not pxl_file:
                raise ValueError("No .pxl file found in zip archive")
            
            if not public_key_file:
                raise ValueError("No public_key.bin found in zip archive")
            
            return pxl_file, public_key_file
            
        except Exception as e:
            self.cleanup_temp_dir()
            raise e
    
    def open_file(self):
        filepath = filedialog.askopenfilename(
            title="Select .pxl or .zip file",
            filetypes=[
                ("Pixealed/Zip files", "*.pxl *.zip"),
                ("Pixealed files", "*.pxl"),
                ("Zip files", "*.zip"),
                ("All files", "*.*")
            ]
        )
        
        if filepath:
            self.load_file(filepath)
    
    def load_file(self, filepath):
        try:
            # Determine if it's a zip file
            if filepath.lower().endswith('.zip'):
                self.status_label.config(text="📦 Extracting zip archive...", fg="#ff9800")
                self.root.update()
                
                pxl_file, public_key_file = self.extract_zip(filepath)
                
                # Load public key from extracted file
                with open(public_key_file, "rb") as f:
                    public_key = f.read()
                
                self.status_label.config(text="✓ Zip extracted, public key loaded", fg="#4caf50")
                self.root.update()
                
            else:
                # Direct .pxl file - look for public_key.bin in same directory or current directory
                pxl_file = filepath
                public_key = None
                
                # Try same directory as .pxl file
                pxl_dir = os.path.dirname(filepath)
                public_key_path = os.path.join(pxl_dir, "public_key.bin")
                
                if os.path.exists(public_key_path):
                    with open(public_key_path, "rb") as f:
                        public_key = f.read()
                # Try current directory
                elif os.path.exists("public_key.bin"):
                    with open("public_key.bin", "rb") as f:
                        public_key = f.read()
            
            # Verify and load the .pxl file
            self.load_pxl_file(pxl_file, public_key)
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to load file:\n\n{str(e)}"
            )
            self.status_label.config(text="✗ Error loading file", fg="#f44336")
            self.cleanup_temp_dir()
    
    def load_pxl_file(self, filepath, public_key):
        try:
            if not public_key:
                response = messagebox.askyesno(
                    "No Public Key",
                    "public_key.bin not found!\n\n"
                    "Without the public key, signature verification cannot be performed.\n"
                    "The image may have been tampered with.\n\n"
                    "Continue anyway (NOT RECOMMENDED)?",
                    icon='warning'
                )
                if not response:
                    self.cleanup_temp_dir()
                    return
            
            # STEP 1: VERIFY integrity and authenticity
            if public_key:
                self.status_label.config(text="🔍 Verifying signature...", fg="#ff9800")
                self.root.update()
                
                is_valid = verify_pxl(filepath, public_key)
                
                if not is_valid:
                    messagebox.showerror(
                        "Verification Failed",
                        "⚠️ TAMPERED FILE DETECTED!\n\n"
                        "The .pxl file has been modified or corrupted.\n"
                        "Signature verification failed.\n\n"
                        "DO NOT TRUST THIS IMAGE!"
                    )
                    self.status_label.config(text="✗ Verification failed", fg="#f44336")
                    self.cleanup_temp_dir()
                    return
                
                self.status_label.config(text="✓ Verified - Image is authentic", fg="#4caf50")
                self.root.update()
            
            # STEP 2: DECRYPT and display (only if verified)
            image_bytes, manifest = read_pxl(filepath)
            
            # Display image
            image = Image.open(io.BytesIO(image_bytes))
            self.display_image(image)
            
            self.current_image = image
            self.current_metadata = manifest
            
            messagebox.showinfo(
                "Success",
                "✓ Image verified and decrypted successfully!\n\n"
                "The image is authentic and has not been tampered with."
            )
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to process .pxl file:\n\n{str(e)}"
            )
            self.status_label.config(text="✗ Error", fg="#f44336")
        finally:
            # Clean up temp directory after successful load
            self.cleanup_temp_dir()
    
    def display_image(self, image):
        # Resize image to fit display
        display_width = 900
        display_height = 500
        
        img_width, img_height = image.size
        ratio = min(display_width/img_width, display_height/img_height)
        
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(resized_image)
        
        self.image_label.config(image=photo, text="")
        self.image_label.image = photo  # Keep reference
    
    def __del__(self):
        """Cleanup on exit"""
        self.cleanup_temp_dir()


def main():
    root = tk.Tk()
    app = PxlViewer(root)
    
    # Cleanup temp directory on window close
    def on_closing():
        app.cleanup_temp_dir()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()