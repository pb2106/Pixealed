"""
Pixealed - Unified GUI Tool
Convert images to tamper-proof .pxl format and view encrypted images
"""

import os
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from modules.converter import pack_image, verify_pxl, read_pxl
from modules.crypto import generate_keypair
from datetime import datetime
from PIL import Image, ImageTk
import io
import tempfile
import shutil
import threading

# Import from your pxl_converter modules

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
            text="Pixealed",
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
        self.notebook.add(self.converter_frame, text="Convert to .pxl  ")
        self.setup_converter_tab()
        
        # Viewer Tab
        self.viewer_frame = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(self.viewer_frame, text="View .pxl Files  ")
        self.setup_viewer_tab()
        
        # About Tab
        self.about_frame = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(self.about_frame, text="About  ")
        self.setup_about_tab()
    
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
        
        # We handle key gen automatically now
        # self.generate_keys_var = tk.BooleanVar(value=True)
        
        # Convert Button
        self.convert_btn = tk.Button(
            self.converter_frame,
            text="Convert to .pxl",
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
            text="Open .pxl File",
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
            text="No image loaded\n\nClick 'Open .pxl File' to decrypt and view an image",
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
            text="Image Metadata:",
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
    
    def setup_about_tab(self):
        about_container = tk.Frame(self.about_frame, bg="#1a1a2e")
        about_container.pack(pady=20, padx=40, fill=tk.BOTH, expand=True)
        
        tk.Label(
            about_container,
            text="What is Pixealed?",
            font=("Arial", 20, "bold"),
            fg="#bb86fc",
            bg="#1a1a2e"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        about_text = (
            "Pixealed is a high-security image encryption and verification utility designed to ensure absolute data integrity and private distribution of visual media. In an era where digital tampering and spoofing are rampant, Pixealed guarantees that the image you encrypt remains mathematically untampered with. By uniting state-of-the-art cryptographic primitives into a specialized '.pxl' container, the software provides non-repudiation, tamper-evidence, and strict confidentiality.\n\n"
            
            "Why XChaCha20-Poly1305?\n"
            "At the core of our encryption layer lies the XChaCha20-Poly1305 cipher suite. Unlike older block ciphers such as AES (which can suffer from cache-timing vulnerability without hardware acceleration), XChaCha20 is a stream cipher that executes with immense speed and consistent timing across all platforms. This ensures rendering large image files is nearly instantaneous. Crucially, the 'Poly1305' component provides Authenticated Encryption with Associated Data (AEAD). This means a cryptographic MAC (Message Authentication Code) is generated alongside the ciphertext. If an attacker attempts to flip a single bit of the encrypted image, the Poly1305 authentication check will fail before decryption even begins, neutralizing chosen-ciphertext attacks. Furthermore, the 'X' (eXtended) version of ChaCha20 uses a massive 192-bit nonce, ensuring that random nonce collisions—which normally destroy the security of stream ciphers—are mathematically impossible.\n\n"
            
            "The Role of Merkle Trees in Granular Verification:\n"
            "While Poly1305 secures the encryption layer, Pixealed employs a Merkle Tree architecture to verify the core structural integrity of the raw image data itself. When an image is packaged, it is split into discrete 256 KB chunks. Each chunk is individually processed through a cryptographic hash function to create a 'leaf' node. Pairs of leaves are then hashed together recursively until they converge into a single, master 'Root Hash' that uniquely fingerprints the entire image. This design serves two vital purposes: first, if even one solitary byte (a single altered pixel) is modified in the media, a cascading avalanche effect completely invalidates the root hash. Second, it embeds resistance against localized corruption, proving unequivocally that the payload perfectly matches its original state at the time of signing.\n\n"
            
            "Digital Signatures (Ed25519) & Key Management:\n"
            "To provide irrefutable proof of origin, the Merkle Root, along with critical image metadata, is bound together into a JSON manifest. This manifest is then cryptographically signed using an Ed25519 elliptic-curve public-key signature scheme. Ed25519 is celebrated for its immunity to side-channel attacks and small, lightning-fast 64-byte signatures. Upon running Pixealed for the first time, a local Ed25519 keypair is automatically generated and securely stored in your './keys' directory as a `.bin` file. When you encrypt an image, the software binds the public key seamlessly into the proprietary `.pxl` binary structure. \n\n"
            
            "When the file is delivered to a recipient, the Pixealed viewer transparently extracts the signature, embeds the public key, and verifies the manifest against the encrypted Merkle Tree. If any parameter has been altered—be it the metadata, the tree root, or the underlying pixel data—the verification chain snaps, throwing a warning and blocking the tampered file. This complete zero-trust lifecycle ensures that what was exported is exactly what is viewed."
        )
        
        text_widget = tk.Text(
            about_container,
            font=("Arial", 12),
            bg="#1a1a2e",
            fg="white",
            wrap=tk.WORD,
            relief=tk.FLAT,
            height=20
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, about_text)
        text_widget.config(state=tk.DISABLED)

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
            output_pxl = base_name + ".pxl"
            
            self.root.after(0, lambda: self.log(f" Input:  {os.path.basename(input_file)}"))
            self.root.after(0, lambda: self.log(f" Output: {os.path.basename(output_pxl)}"))
            
            # Load existing key or generate
            keys_dir = "./keys"
            os.makedirs(keys_dir, exist_ok=True)
            existing_keys = [f for f in os.listdir(keys_dir) if f.startswith("signing_key_")]
            
            if existing_keys:
                self.root.after(0, lambda: self.log("\n Loading existing signing key..."))
                signing_key_path = os.path.join(keys_dir, existing_keys[0])
                with open(signing_key_path, "rb") as f:
                    signing_key = f.read()
                self.root.after(0, lambda: self.log(f" Loaded {existing_keys[0]}"))
            else:
                self.root.after(0, lambda: self.log("\n Generating new Ed25519 keypair..."))
                signing_key, public_key = generate_keypair()
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                signing_key_path = f"{keys_dir}/signing_key_{timestamp}.bin"
                
                with open(signing_key_path, "wb") as f:
                    f.write(signing_key)
                
                self.root.after(0, lambda: self.log(f" Signing key generated and saved"))
            
            # Convert
            self.root.after(0, lambda: self.log("\n Converting to encrypted .pxl format..."))
            pack_image(input_file, output_pxl, signing_key)
            
            original_size = os.path.getsize(input_file)
            pxl_size = os.path.getsize(output_pxl)
            overhead = pxl_size - original_size
            
            self.root.after(0, lambda: self.log(f"   .pxl file created"))
            self.root.after(0, lambda: self.log(f"\n Statistics:"))
            self.root.after(0, lambda: self.log(f"   Original: {format_bytes(original_size)}"))
            self.root.after(0, lambda: self.log(f"   .pxl:     {format_bytes(pxl_size)}"))
            self.root.after(0, lambda: self.log(f"   Overhead: {format_bytes(overhead)} ({overhead/original_size*100:.1f}%)"))
            
            # Verify
            if self.verify_var.get():
                self.root.after(0, lambda: self.log("\n Verifying integrity..."))
                is_valid = verify_pxl(output_pxl)
                
                if is_valid:
                    self.root.after(0, lambda: self.log("   Verification PASSED"))
                else:
                    self.root.after(0, lambda: self.log("   Verification FAILED"))
                    if os.path.exists(output_pxl):
                        os.remove(output_pxl)
                    return
            
            self.root.after(0, lambda: self.log("\n Conversion complete!"))
            self.root.after(0, lambda: self.log(f" Output: {output_pxl}"))
            self.root.after(0, lambda: self.log(f" Keys logic completed at: {signing_key_path}"))
            
            self.root.after(0, lambda: messagebox.showinfo(
                "Success",
                f"Image encrypted successfully!\n\nOutput: {os.path.basename(output_pxl)}"
            ))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.log(f"\n Error: {msg}"))
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("Conversion Error", msg))
        finally:
            self.root.after(0, lambda: self.convert_btn.config(state=tk.NORMAL))
    
    def open_file(self):
        filepath = filedialog.askopenfilename(
            title="Select .pxl file",
            filetypes=[("Pixealed files", "*.pxl"), ("All files", "*.*")]
        )
        
        if filepath:
            ext = os.path.splitext(filepath)[1].lower()
            if ext == ".pxl":
                self.load_pxl_file(filepath)
            else:
                messagebox.showwarning("Invalid File", "Please select a .pxl file.")
    
    def load_pxl_file(self, filepath):
        try:
            # Verify the file (will use embedded key)
            is_valid = verify_pxl(filepath)
            
            if not is_valid:
                messagebox.showerror(
                    "Verification Failed",
                    "File verification FAILED!\n\nThe .pxl file may be corrupted, tampered with, or lack a valid signature profile."
                )
                return
            else:
                messagebox.showinfo(
                    "Verification Passed",
                    "File verification PASSED!\n\nThe signature is valid and untampered."
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