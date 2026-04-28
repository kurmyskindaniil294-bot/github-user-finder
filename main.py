# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from threading import Thread
from datetime import datetime

class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder - Maria Alekseeva")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        self.favorites_file = "favorites.json"
        self.favorites = self.load_favorites()
        self.search_var = tk.StringVar()
        self.current_results = []
        
        self.setup_ui()
        self.update_favorites_list()
    
    def load_favorites(self):
        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_favorites(self):
        with open(self.favorites_file, 'w', encoding='utf-8') as f:
            json.dump(self.favorites, f, ensure_ascii=False, indent=2)
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(main_frame, text="GitHub User Finder", font=("Arial", 20, "bold"))
        title.pack(pady=10)
        
        author = ttk.Label(main_frame, text="Author: Maria Alekseeva", font=("Arial", 10))
        author.pack()
        
        search_frame = ttk.LabelFrame(main_frame, text="Search User", padding="10")
        search_frame.pack(fill=tk.X, pady=10)
        
        search_inner = ttk.Frame(search_frame)
        search_inner.pack(fill=tk.X)
        
        ttk.Label(search_inner, text="Enter GitHub username:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_inner, textvariable=self.search_var, width=50)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind("<Return>", lambda e: self.search_user())
        
        self.search_btn = ttk.Button(search_inner, text="Search", command=self.search_user)
        self.search_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(search_frame, text="Ready to search", foreground="green")
        self.status_label.pack(pady=5)
        
        content = ttk.Frame(main_frame)
        content.pack(fill=tk.BOTH, expand=True, pady=10)
        
        left = ttk.LabelFrame(content, text="Search Results", padding="5")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        columns = ("username", "name", "public_repos", "followers", "action")
        self.tree = ttk.Treeview(left, columns=columns, show="headings", height=15)
        
        self.tree.heading("username", text="Username")
        self.tree.heading("name", text="Name")
        self.tree.heading("public_repos", text="Repos")
        self.tree.heading("followers", text="Followers")
        self.tree.heading("action", text="Action")
        
        self.tree.column("username", width=150)
        self.tree.column("name", width=200)
        self.tree.column("public_repos", width=100, anchor="center")
        self.tree.column("followers", width=100, anchor="center")
        self.tree.column("action", width=100, anchor="center")
        
        scroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<ButtonRelease-1>", self.on_click)
        
        right = ttk.LabelFrame(content, text="Favorites", padding="5")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10)
        
        self.fav_listbox = tk.Listbox(right, width=30, height=20, font=("Arial", 10))
        self.fav_listbox.pack(fill=tk.BOTH, expand=True)
        
        fav_btn_frame = ttk.Frame(right)
        fav_btn_frame.pack(fill=tk.X, pady=5)
        
        self.remove_fav_btn = ttk.Button(fav_btn_frame, text="Remove from Favorites", command=self.remove_from_favorites)
        self.remove_fav_btn.pack(fill=tk.X)
    
    def search_user(self):
        username = self.search_var.get().strip()
        
        if not username:
            messagebox.showwarning("Error", "Search field cannot be empty!")
            return
        
        self.status_label.config(text="Searching...", foreground="orange")
        self.search_btn.config(state=tk.DISABLED)
        self.search_entry.config(state=tk.DISABLED)
        
        Thread(target=self.api_search, args=(username,), daemon=True).start()
    
    def api_search(self, username):
        try:
            url = f"https://api.github.com/users/{username}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.root.after(0, self.display_result, data)
                self.root.after(0, self.update_status, f"User found: {data.get('login')}", "green")
            elif response.status_code == 404:
                self.root.after(0, self.update_status, "User not found", "red")
                self.root.after(0, messagebox.showerror, "Error", f"User '{username}' not found on GitHub")
            else:
                self.root.after(0, self.update_status, f"API Error: {response.status_code}", "red")
        except requests.exceptions.Timeout:
            self.root.after(0, self.update_status, "Connection timeout", "red")
        except Exception as e:
            self.root.after(0, self.update_status, f"Error: {str(e)}", "red")
        finally:
            self.root.after(0, self.enable_search)
    
    def display_result(self, user):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        login = user.get('login', 'N/A')
        name = user.get('name', 'Not specified') or 'Not specified'
        repos = user.get('public_repos', 0)
        followers = user.get('followers', 0)
        
        action = "Add to Favorites" if login not in self.favorites else "In Favorites"
        
        self.tree.insert("", tk.END, iid=login, values=(login, name, repos, followers, action))
        self.current_results = [user]
    
    def on_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#5":
                item = self.tree.identify_row(event.y)
                if item:
                    self.add_to_favorites(item)
    
    def add_to_favorites(self, username):
        if username in self.favorites:
            messagebox.showinfo("Info", f"User {username} is already in favorites")
            return
        
        user_data = None
        for user in self.current_results:
            if user.get('login') == username:
                user_data = user
                break
        
        if user_data:
            self.favorites[username] = {
                "login": user_data.get('login'),
                "name": user_data.get('name', 'Not specified'),
                "public_repos": user_data.get('public_repos', 0),
                "followers": user_data.get('followers', 0),
                "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.save_favorites()
            self.update_favorites_list()
            self.update_status(f"Added to favorites: {username}", "green")
            self.update_action_button(username, "In Favorites")
    
    def remove_from_favorites(self):
        selection = self.fav_listbox.curselection()
        if not selection:
            messagebox.showwarning("Error", "Select a user to remove")
            return
        
        username = self.fav_listbox.get(selection[0])
        if username in self.favorites:
            del self.favorites[username]
            self.save_favorites()
            self.update_favorites_list()
            self.update_status(f"Removed from favorites: {username}", "orange")
            self.update_action_button(username, "Add to Favorites")
    
    def update_favorites_list(self):
        self.fav_listbox.delete(0, tk.END)
        for username in self.favorites.keys():
            self.fav_listbox.insert(tk.END, username)
    
    def update_action_button(self, username, text):
        for item in self.tree.get_children():
            if item == username:
                values = list(self.tree.item(item, 'values'))
                values[4] = text
                self.tree.item(item, values=values)
                break
    
    def update_status(self, message, color):
        self.status_label.config(text=message, foreground=color)
    
    def enable_search(self):
        self.search_btn.config(state=tk.NORMAL)
        self.search_entry.config(state=tk.NORMAL)

def main():
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()

if __name__ == "__main__":
    main()