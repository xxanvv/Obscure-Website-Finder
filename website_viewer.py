import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import webbrowser
import io
import os
import re
import asyncio
import threading
import concurrent.futures
import time
from playwright.async_api import async_playwright
import nest_asyncio

nest_asyncio.apply()

class DarkTheme:
    BG_COLOR = "#1e1e1e"
    FG_COLOR = "#ffffff"
    ACCENT_COLOR = "#3d3d3d"
    HOVER_COLOR = "#4a4a4a"
    BUTTON_BG = "#2d2d2d"
    PREVIEW_BG = "#2a2a2a"

class WebsiteViewer(tk.Tk):
    WEBSITES_PER_PAGE = 100
    GRID_COLUMNS = 5

    def __init__(self):
        super().__init__()

        self.title("Found Websites Viewer")
        self.geometry("1200x800")
        self.configure(bg=DarkTheme.BG_COLOR)
        
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=15)
        self.screenshot_futures = {}
        
        self.current_page = 0
        self.total_pages = 0
        
        self.setup_theme()
        self.setup_ui()
        
        self.websites = []
        self.load_websites()
        
        self.after(50, self.check_screenshots)

    def setup_theme(self):
        """Configure the dark theme for widgets"""
        self.style = ttk.Style()
        self.style.configure("Dark.TFrame", background=DarkTheme.BG_COLOR)
        self.style.configure("Dark.TLabel", 
                           background=DarkTheme.BG_COLOR, 
                           foreground=DarkTheme.FG_COLOR)
        self.style.configure("Dark.TButton",
                           background=DarkTheme.BUTTON_BG,
                           foreground=DarkTheme.FG_COLOR)

    def setup_ui(self):
        """Initialize all UI components"""
        self.main_container = ttk.Frame(self, style="Dark.TFrame")
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.main_container, 
                              height=600,
                              bg=DarkTheme.BG_COLOR,
                              highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.main_container, 
                                     orient=tk.VERTICAL, 
                                     command=self.canvas.yview)
        
        self.scrollable_frame = ttk.Frame(self.canvas, style="Dark.TFrame")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.create_pagination_controls()
        
        self.bind_mousewheel()

    def create_pagination_controls(self):
        self.pagination_frame = ttk.Frame(self, style="Dark.TFrame")
        self.pagination_frame.pack(side=tk.BOTTOM, pady=10)
        
        self.prev_button = ttk.Button(self.pagination_frame, 
                                    text="Previous",
                                    style="Dark.TButton",
                                    command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT, padx=5)
        
        self.page_label = ttk.Label(self.pagination_frame,
                                  style="Dark.TLabel",
                                  text="Page 1 of 1")
        self.page_label.pack(side=tk.LEFT, padx=20)
        
        self.next_button = ttk.Button(self.pagination_frame,
                                    text="Next",
                                    style="Dark.TButton",
                                    command=self.next_page)
        self.next_button.pack(side=tk.LEFT, padx=5)

    def bind_mousewheel(self):
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta/120)), "units")
        
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def load_websites(self):
        try:
            with open('found_websites.txt', 'r') as f:
                content = f.read()
                
            if not os.path.exists('thumbnails'):
                os.makedirs('thumbnails')
                
            website_blocks = content.split('-' * 50)
            for block in website_blocks:
                if 'IP:' in block:
                    ip_match = re.search(r'IP: ([\d\.]+)', block)
                    protocol_match = re.search(r'Protocol: (HTTP[S]?)', block)
                    title_match = re.search(r'Title: (.+)', block)
                    
                    if ip_match:
                        website = {
                            'ip': ip_match.group(1),
                            'protocol': protocol_match.group(1) if protocol_match else 'HTTP',
                            'title': title_match.group(1) if title_match else 'No Title'
                        }
                        self.websites.append(website)
            
            self.update_page()
            
        except FileNotFoundError:
            messagebox.showerror("Error", "found_websites.txt not found!")
            self.destroy()

    def update_page(self):
        try:
            old_futures = list(self.screenshot_futures.keys())
            for future in old_futures:
                if not future.done():
                    future.cancel()
            self.screenshot_futures.clear()
            
            for widget in self.scrollable_frame.winfo_children():
                for child in widget.winfo_children():
                    child.destroy()
                widget.destroy()
            
            import gc
            gc.collect()
            
            start_idx = self.current_page * self.WEBSITES_PER_PAGE
            end_idx = start_idx + self.WEBSITES_PER_PAGE
            page_websites = self.websites[start_idx:end_idx]
            
            for idx, website in enumerate(page_websites):
                row = idx // self.GRID_COLUMNS
                col = idx % self.GRID_COLUMNS
                
                grid_frame = ttk.Frame(self.scrollable_frame, style="Dark.TFrame")
                grid_frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
                grid_frame.website_ip = website['ip']
                
                self.create_website_preview(grid_frame, website)
            
            self.total_pages = (len(self.websites) - 1) // self.WEBSITES_PER_PAGE + 1
            self.page_label.config(text=f"Page {self.current_page + 1} of {self.total_pages}")
            
            self.prev_button.state(['!disabled'] if self.current_page > 0 else ['disabled'])
            self.next_button.state(['!disabled'] if self.current_page < self.total_pages - 1 else ['disabled'])
            
            for i in range(self.GRID_COLUMNS):
                self.scrollable_frame.grid_columnconfigure(i, weight=1)
                
        except Exception as e:
            print(f"Error updating page: {e}")
            messagebox.showerror("Error", f"Failed to update page: {str(e)}")
            self.current_page = 0

    def create_website_preview(self, frame, website):
        preview_frame = ttk.Frame(frame, style="Dark.TFrame")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        url = f"{website['protocol'].lower()}://{website['ip']}"
        
        img = Image.new('RGB', (200, 150), color=DarkTheme.ACCENT_COLOR)
        draw = ImageDraw.Draw(img)
        draw.text((70, 75), "Loading...", fill=DarkTheme.FG_COLOR)
        photo = ImageTk.PhotoImage(img)
        
        img_label = tk.Label(preview_frame, 
                           image=photo,
                           bg=DarkTheme.PREVIEW_BG)
        img_label.image = photo
        img_label.pack(pady=5)
        
        title_label = ttk.Label(preview_frame, 
                             text=website['title'],
                             style="Dark.TLabel",
                             wraplength=200)
        title_label.pack(pady=(0,2))
        
        ip_label = ttk.Label(preview_frame,
                          text=website['ip'],
                          style="Dark.TLabel")
        ip_label.pack(pady=(0,2))
        
        visit_btn = ttk.Button(preview_frame, 
                             text="Visit Website",
                             style="Dark.TButton",
                             command=lambda u=url: webbrowser.open(u))
        visit_btn.pack(pady=(0,5))
        
        future = self.executor.submit(self.capture_screenshot, url, website['ip'])
        self.screenshot_futures[future] = (img_label, url)

    def check_screenshots(self):
        try:
            if not self.winfo_exists():
                return
                
            completed = [future for future in list(self.screenshot_futures.keys()) 
                        if future.done()]
            
            for future in completed:
                if future not in self.screenshot_futures:
                    continue
                    
                img_label, url = self.screenshot_futures[future]
                try:
                    if not img_label.winfo_exists():
                        continue
                        
                    thumbnail_path = future.result()
                    if thumbnail_path and os.path.exists(thumbnail_path):
                        img = Image.open(thumbnail_path)
                        img.thumbnail((200, 150))
                        photo = ImageTk.PhotoImage(img)
                        img_label.configure(image=photo)
                        img_label.image = photo
                except Exception as e:
                    print(f"Error loading thumbnail for {url}: {e}")
                finally:
                    self.screenshot_futures.pop(future, None)
            
            if self.winfo_exists():
                self.after(50, self.check_screenshots)
                
        except Exception as e:
            print(f"Error in check_screenshots: {e}")
            if self.winfo_exists():
                self.after(50, self.check_screenshots)

    def capture_screenshot(self, url, ip):
        """Run async screenshot capture in the event loop"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.capture_screenshot_async(url, ip))
        finally:
            loop.close()

    async def capture_screenshot_async(self, url, ip):
        thumbnail_path = f'thumbnails/{ip}.png'
        
        if os.path.exists(thumbnail_path):
            return thumbnail_path

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    args=['--ignore-certificate-errors', '--disable-web-security']
                )
                context = await browser.new_context(
                    ignore_https_errors=True,
                    viewport={"width": 800, "height": 600}
                )
                page = await context.new_page()
                try:
                    await page.goto(url, timeout=10000, wait_until='domcontentloaded')
                    await page.wait_for_timeout(1000)
                    await page.screenshot(path=thumbnail_path)
                    return thumbnail_path
                except Exception as e:
                    error_msg = str(e)
                    if "ERR_CERT" in error_msg:
                        print(f"Certificate error for {url}, attempting anyway")
                        self.create_error_image(thumbnail_path, "Certificate Error")
                    elif "Timeout" in error_msg:
                        print(f"Timeout error for {url}")
                        self.create_error_image(thumbnail_path, "Timeout")
                    else:
                        print(f"Error capturing screenshot for {url}: {e}")
                        self.create_error_image(thumbnail_path, "Error Loading")
                    return thumbnail_path
                finally:
                    await context.close()
                    await browser.close()
        except Exception as e:
            print(f"Browser error for {url}: {e}")
            self.create_error_image(thumbnail_path, "Screenshot Failed")
            return thumbnail_path

    def create_error_image(self, path, text):
        img = Image.new('RGB', (200, 150), color=DarkTheme.ACCENT_COLOR)
        draw = ImageDraw.Draw(img)
        draw.text((50, 75), text, fill=DarkTheme.FG_COLOR)
        img.save(path)

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_page()
            self.canvas.yview_moveto(0)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page()
            self.canvas.yview_moveto(0)

    def __del__(self):
        self.executor.shutdown(wait=False)

def show_viewer():
    app = WebsiteViewer()
    app.mainloop()

if __name__ == "__main__":
    show_viewer()