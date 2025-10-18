"""
Pixealed - Unified GUI Tool
Convert images to tamper-proof .pxl format and view encrypted images
"""

import os
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from PIL import Image, ImageTk
import io
import tempfile
import shutil
import threading

# Import from your pxl_converter modules
try:
    from modules.converter import pack_image, verify_pxl, read_pxl
    from modules.crypto import generate_keypair
except ImportError:
    def pack_image(*args, **kwargs):
        raise RuntimeError("pack_image() not available — run from full Pixealed project context.")
    def verify_pxl(*args, **kwargs):
        raise RuntimeError("verify_pxl() not available — run from full Pixealed project context.")
    def read_pxl(*args, **kwargs):
        raise RuntimeError("read_pxl() not available — run from full Pixealed project context.")
    def generate_keypair(*args, **kwargs):
        raise RuntimeError("generate_keypair() not available — run from full Pixealed project context.")


def format_bytes(bytes_val):
    """Format bytes as human-readable string"""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.2f} KB"
    else:
        return f"{bytes_val / (1024 * 1024):.2f} MB"


class PixealedApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pixealed - Image Encryption & Viewer")
        self.root.geometry("1200x900")
        self.root.configure(bg="#1a1a2e")
        
        self.current_image = None
        self.current_metadata = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main Title
        title_frame = tk.Frame(self.root, bg="#1a1a2e")
        title_frame.pack(pady=20)
        
        title = tk.Label(
            title_frame,
            text="🔒 Pixealed",
            font=("Arial", 28, "bold"),
            fg="#bb86fc",
            bg="#1a1a2e"
        )
        title.pack()
        
        subtitle = tk.Label(
            title_frame,
            text="Secure Image Encryption & Decryption Tool",
            font=("Arial", 12),
            fg="#9d9d9d",
            bg="#1a1a2e"
        )
        subtitle.pack()
        
        # Create Notebook (Tabs)
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background="#1a1a2e", borderwidth=0)
        style.configure('TNotebook.Tab', background="#2a2a3e", foreground="white", 
                       padding=[20, 10], font=("Arial", 11, "bold"))
        style.map('TNotebook.Tab', background=[('selected', '#bb86fc')],
                 foreground=[('selected', 'white')])
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        # Converter Tab
        self.converter_frame = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(self.converter_frame, text="  🔐 Convert to .pxl  ")
        self.setup_converter_tab()
        
        # Viewer Tab
        self.viewer_frame = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(self.viewer_frame, text="  👁️ View .pxl Files  ")
        self.setup_viewer_tab()
    
    def setup_converter_tab(self):
        # Input Section
        input_frame = tk.Frame(self.converter_frame, bg="#1a1a2e")
        input_frame.pack(pady=20, padx=20, fill=tk.X)
        
        tk.Label(
            input_frame,
            text="Select Image to Encrypt:",
            font=("Arial", 12, "bold"),
            fg="#bb86fc",
            bg="#1a1a2e"
        ).pack(anchor=tk.W, pady=5)
        
        input_btn_frame = tk.Frame(input_frame, bg="#1a1a2e")
        input_btn_frame.pack(fill=tk.X, pady=5)
        
        self.input_label = tk.Label(
            input_btn_frame,
            text="No file selected",
            font=("Arial", 10),
            fg="#9d9d9d",
            bg="#0f0f1e",
            anchor=tk.W,
            padx=10,
            pady=8
        )
        self.input_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Button(
            input_btn_frame,
            text="Browse...",
            font=("Arial", 10, "bold"),
            bg="#bb86fc",
            fg="white",
            activebackground="#9d6fd4",
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.select_input_file
        ).pack(side=tk.RIGHT)
        
        # Options Section
        options_frame = tk.Frame(self.converter_frame, bg="#1a1a2e")
        options_frame.pack(pady=20, padx=20, fill=tk.X)
        
        tk.Label(
            options_frame,
            text="Options:",
            font=("Arial", 12, "bold"),
            fg="#bb86fc",
            bg="#1a1a2e"
        ).pack(anchor=tk.W, pady=5)
        
        self.verify_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options_frame,
            text="Verify file after creation",
            variable=self.verify_var,
            font=("Arial", 10),
            fg="white",
            bg="#1a1a2e",
            selectcolor="#0f0f1e",
            activebackground="#1a1a2e",
            activeforeground="white"
        ).pack(anchor=tk.W, pady=2)
        
        self.generate_keys_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options_frame,
            text="Generate new keypair",
            variable=self.generate_keys_var,
            font=("Arial", 10),
            fg="white",
            bg="#1a1a2e",
            selectcolor="#0f0f1e",
            activebackground="#1a1a2e",
            activeforeground="white"
        ).pack(anchor=tk.W, pady=2)
        
        # Convert Button
        self.convert_btn = tk.Button(
            self.converter_frame,
            text="🔒 Convert to .pxl",
            font=("Arial", 14, "bold"),
            bg="#bb86fc",
            fg="white",
            activebackground="#9d6fd4",
            activeforeground="white",
            padx=40,
            pady=15,
            cursor="hand2",
            command=self.convert_image,
            state=tk.DISABLED
        )
        self.convert_btn.pack(pady=20)
        
        # Log Section
        log_frame = tk.Frame(self.converter_frame, bg="#1a1a2e")
        log_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        tk.Label(
            log_frame,
            text="Conversion Log:",
            font=("Arial", 11, "bold"),
            fg="#bb86fc",
            bg="#1a1a2e"
        ).pack(anchor=tk.W, pady=5)
        
        # Add scrollbar
        log_scroll = tk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(
            log_frame,
            height=12,
            font=("Courier", 9),
            bg="#0f0f1e",
            fg="#03dac6",
            insertbackground="#03dac6",
            relief=tk.FLAT,
            padx=10,
            pady=10,
            yscrollcommand=log_scroll.set
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)
        self.log_text.config(state=tk.DISABLED)
        
        self.selected_input_file = None
    
    def setup_viewer_tab(self):
        # Open Button
        open_btn = tk.Button(
            self.viewer_frame,
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
        open_btn.pack(pady=20)
        
        # Image Display Frame
        image_frame = tk.Frame(self.viewer_frame, bg="#0f0f1e", relief=tk.SUNKEN, bd=2)
        image_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        self.image_label = tk.Label(
            image_frame,
            text="No image loaded\n\nClick 'Open .pxl or .zip File' to decrypt and view an image",
            font=("Arial", 14),
            fg="#6d6d6d",
            bg="#0f0f1e"
        )
        self.image_label.pack(expand=True)
        
        # Metadata Frame
        metadata_frame = tk.Frame(self.viewer_frame, bg="#1a1a2e")
        metadata_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(
            metadata_frame,
            text="📷 Image Metadata:",
            font=("Arial", 11, "bold"),
            fg="#bb86fc",
            bg="#1a1a2e"
        ).pack(anchor=tk.W, pady=5)
        
        self.metadata_text = tk.Text(
            metadata_frame,
            height=6,
            font=("Courier", 9),
            bg="#0f0f1e",
            fg="#bb86fc",
            insertbackground="#bb86fc",
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.metadata_text.pack(fill=tk.BOTH, expand=True)
        self.metadata_text.config(state=tk.DISABLED)
    
    def select_input_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Image to Encrypt",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff"),
                ("All files", "*.*")
            ]
        )
        
        if filepath:
            self.selected_input_file = filepath
            self.input_label.config(text=os.path.basename(filepath), fg="white")
            self.convert_btn.config(state=tk.NORMAL)
            self.log("Selected: " + filepath)
    
    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def convert_image(self):
        if not self.selected_input_file:
            messagebox.showwarning("No File", "Please select an image file first.")
            return
        
        # Run conversion in thread to avoid freezing UI
        thread = threading.Thread(target=self._convert_image_thread)
        thread.daemon = True
        thread.start()
    
    def _convert_image_thread(self):
        try:
            self.root.after(0, lambda: self.convert_btn.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.log("\n=== Starting Conversion ==="))
            
            # Prepare paths
            input_file = self.selected_input_file
            base_name = os.path.splitext(input_file)[0]
            output_zip = base_name + ".zip"
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            signing_key_path = f"./keys/signing_key_{timestamp}.bin"
            public_key_path = f"./keys/public_key_{timestamp}.bin"
            temp_pxl = f"temp_{timestamp}.pxl"
            
            self.root.after(0, lambda: self.log(f"📁 Input:  {os.path.basename(input_file)}"))
            self.root.after(0, lambda: self.log(f"📦 Output: {os.path.basename(output_zip)}"))
            
            # Generate or load keys
            if self.generate_keys_var.get():
                self.root.after(0, lambda: self.log("\n🔑 Generating new Ed25519 keypair..."))
                signing_key, public_key = generate_keypair()
                
                os.makedirs(os.path.dirname(signing_key_path) or '.', exist_ok=True)
                
                with open(signing_key_path, "wb") as f:
                    f.write(signing_key)
                with open(public_key_path, "wb") as f:
                    f.write(public_key)
                
                self.root.after(0, lambda: self.log(f"   ✓ Keys generated and saved"))
            else:
                self.root.after(0, lambda: self.log("❌ Error: Key loading not implemented in GUI mode"))
                return
            
            # Convert
            self.root.after(0, lambda: self.log("\n🔒 Converting to encrypted .pxl format..."))
            pack_image(input_file, temp_pxl, signing_key)
            
            original_size = os.path.getsize(input_file)
            pxl_size = os.path.getsize(temp_pxl)
            overhead = pxl_size - original_size
            
            self.root.after(0, lambda: self.log(f"   ✓ .pxl file created"))
            self.root.after(0, lambda: self.log(f"\n📊 Statistics:"))
            self.root.after(0, lambda: self.log(f"   Original: {format_bytes(original_size)}"))
            self.root.after(0, lambda: self.log(f"   .pxl:     {format_bytes(pxl_size)}"))
            self.root.after(0, lambda: self.log(f"   Overhead: {format_bytes(overhead)} ({overhead/original_size*100:.1f}%)"))
            
            # Verify
            if self.verify_var.get():
                self.root.after(0, lambda: self.log("\n🔍 Verifying integrity..."))
                is_valid = verify_pxl(temp_pxl, public_key)
                
                if is_valid:
                    self.root.after(0, lambda: self.log("   ✓ Verification PASSED"))
                else:
                    self.root.after(0, lambda: self.log("   ❌ Verification FAILED"))
                    if os.path.exists(temp_pxl):
                        os.remove(temp_pxl)
                    return
            
            # Package
            self.root.after(0, lambda: self.log("\n📦 Packaging into .zip..."))
            with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                base_pxl_name = os.path.splitext(os.path.basename(input_file))[0] + ".pxl"
                zipf.write(temp_pxl, base_pxl_name)
                zipf.write(public_key_path, "public_key.bin")
            
            zip_size = os.path.getsize(output_zip)
            self.root.after(0, lambda: self.log(f"   ✓ Created '{os.path.basename(output_zip)}' ({format_bytes(zip_size)})"))
            
            # Cleanup
            if os.path.exists(temp_pxl):
                os.remove(temp_pxl)
            
            self.root.after(0, lambda: self.log("\n✅ Conversion complete!"))
            self.root.after(0, lambda: self.log(f"📦 Package: {output_zip}"))
            self.root.after(0, lambda: self.log(f"🔑 Keys: {os.path.dirname(signing_key_path)}/"))
            
            self.root.after(0, lambda: messagebox.showinfo(
                "Success",
                f"Image encrypted successfully!\n\nOutput: {os.path.basename(output_zip)}"
            ))
            
        except Exception as e:
            self.root.after(0, lambda: self.log(f"\n❌ Error: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Conversion Error", str(e)))
        finally:
            self.root.after(0, lambda: self.convert_btn.config(state=tk.NORMAL))
    
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
            
            pxl_file = None
            pubkey_file = None
            for name in os.listdir(temp_dir):
                if name.endswith(".pxl"):
                    pxl_file = os.path.join(temp_dir, name)
                elif name.endswith(".pub") or "public" in name.lower():
                    pubkey_file = os.path.join(temp_dir, name)
            
            if not pxl_file:
                raise FileNotFoundError("No .pxl file found inside ZIP.")
            
            self.load_pxl_file(pxl_file, pubkey_file)
        
        except zipfile.BadZipFile:
            messagebox.showerror("Invalid ZIP", "The selected ZIP file is corrupted or invalid.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open bundle:\n\n{str(e)}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def load_pxl_file(self, filepath, public_key_path=None):
        try:
            # Verify the file first if we have a public key
            if public_key_path and os.path.exists(public_key_path):
                with open(public_key_path, "rb") as f:
                    public_key = f.read()
                
                is_valid = verify_pxl(filepath, public_key)
                
                if not is_valid:
                    messagebox.showerror(
                        "Verification Failed",
                        "⚠️ File verification FAILED!\n\nThe .pxl file may be corrupted or tampered with."
                    )
                    return
                else:
                    messagebox.showinfo(
                        "Verification Passed",
                        "✓ File verification PASSED!\n\nThe file is authentic and untampered."
                    )
            
            # Read and decrypt the file
            image_bytes, manifest = read_pxl(filepath)
            
            image = Image.open(io.BytesIO(image_bytes))
            self.display_image(image)
            self.display_metadata(manifest.get("metadata", {}))
            
            self.current_image = image
            self.current_metadata = manifest
            
        except Exception as e:
            messagebox.showerror(
                "Decryption Error",
                f"Failed to decrypt .pxl file:\n\n{str(e)}"
            )
    
    def display_image(self, image):
        display_width = 1000
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
            for key, value in metadata.items():
                self.metadata_text.insert(tk.END, f"{key:20s}: {value}\n")
        else:
            self.metadata_text.insert(tk.END, "No metadata available")
        
        self.metadata_text.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = PixealedApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()