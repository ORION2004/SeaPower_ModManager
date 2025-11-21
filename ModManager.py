import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import configparser
import os
import sys
import re
import shutil
import json
from PIL import Image, ImageTk  # pip install pillow

# ==========================================
# 全局配置与多语言界面词典
# ==========================================
APP_CONFIG_FILE = "ModManagerConfig.json"
PRESET_DIR = "Presets"

# 界面本身的语言文本
UI_LANG_DATA = {
    "cn": {
        "title": "游戏模组管理器",
        "path_settings": "路径设置",
        "game_config": "游戏配置文件:",
        "mod_dir": "模组保存目录:",
        "browse": "浏览...",
        "load_refresh": "读取/刷新",
        "save_config": "保存配置 (覆盖备份)",
        "save_preset": "保存预设",
        "load_preset": "加载预设",
        "font_size": "字体大小:",
        "language": "语言/Language:",
        "mod_list_title": "模组加载顺序 (拖拽排序，双击开关)",
        "col_status": "状态",
        "col_name": "模组名称",
        "col_id": "ID/文件夹",
        "mod_details": "模组详情",
        "no_image": "无图片",
        "status_on": "✅ 开启",
        "status_off": "❌ 关闭",
        "msg_error": "错误",
        "msg_success": "成功",
        "msg_path_err": "路径无效，请检查设置。",
        "msg_load_ok": "已加载 {} 个模组",
        "msg_saved": "配置文件已保存！\n备份文件已覆盖。",
        "msg_backup_fail": "备份失败: {}\n是否继续保存？",
        "msg_preset_saved": "预设已保存。",
        "msg_preset_loaded": "预设加载完成。",
        "msg_preset_missing": "\n\n注意：以下模组在预设中存在但本地未安装：\n",
        "fallback_desc": "该模组无当前语言的简介。"
    },
    "en": {
        "title": "Game Mod Manager",
        "path_settings": "Path Settings",
        "game_config": "Game Config File:",
        "mod_dir": "Mod Directory:",
        "browse": "Browse...",
        "load_refresh": "Load/Refresh",
        "save_config": "Save Config (Overwrite Backup)",
        "save_preset": "Save Preset",
        "load_preset": "Load Preset",
        "font_size": "Font Size:",
        "language": "Language:",
        "mod_list_title": "Load Order (Drag to reorder, Double-click to toggle)",
        "col_status": "Status",
        "col_name": "Mod Name",
        "col_id": "ID/Folder",
        "mod_details": "Details",
        "no_image": "No Image",
        "status_on": "✅ ON",
        "status_off": "❌ OFF",
        "msg_error": "Error",
        "msg_success": "Success",
        "msg_path_err": "Invalid paths. Please check settings.",
        "msg_load_ok": "Loaded {} mods.",
        "msg_saved": "Configuration saved!\nBackup file overwritten.",
        "msg_backup_fail": "Backup failed: {}\nContinue saving?",
        "msg_preset_saved": "Preset saved.",
        "msg_preset_loaded": "Preset loaded.",
        "msg_preset_missing": "\n\nWarning: The following mods are in preset but missing locally:\n",
        "fallback_desc": "No description available for this language."
    }
}

def get_app_path():
    """获取程序运行目录 (兼容 exe)"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

# ==========================================
# 核心数据类 (核心修改部分)
# ==========================================

class ModItem:
    def __init__(self, mod_id, enabled=False):
        self.mod_id = mod_id
        self.enabled = enabled
        self.image_path = None
        
        # 存储所有语言的元数据
        self.meta_data = {
            'cn': {'name': '', 'desc': ''},
            'en': {'name': '', 'desc': ''}
        }

    def load_info(self, workshop_root_path):
        mod_dir = os.path.join(workshop_root_path, self.mod_id)
        if not os.path.exists(mod_dir):
            return

        # 1. 图片
        img_files = [f for f in os.listdir(mod_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if img_files:
            self.image_path = os.path.join(mod_dir, img_files[0])

        # 2. 信息文件
        info_file = os.path.join(mod_dir, "_info.ini")
        if not os.path.exists(info_file):
            # 兼容旧版 txt
            for f in os.listdir(mod_dir):
                if f.startswith("_info") and f.endswith(".txt"):
                    info_file = os.path.join(mod_dir, f)
                    break
        
        if info_file and os.path.exists(info_file):
            self._parse_info(info_file)

    def _parse_info(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            cur_section = None
            
            for line in lines:
                line = line.strip()
                lower_line = line.lower()
                
                # 识别区块
                if lower_line.startswith('[language_cn]'):
                    cur_section = 'cn'
                elif lower_line.startswith('[language_en]'):
                    cur_section = 'en'
                elif line.startswith('[') and line.endswith(']'):
                    cur_section = None # 其他无关区块
                
                # 读取内容
                if cur_section:
                    if line.startswith('Name='):
                        self.meta_data[cur_section]['name'] = line[5:].strip()
                    elif line.startswith('Description='):
                        self.meta_data[cur_section]['desc'] = line[12:].strip()
        except Exception as e:
            print(f"Parsing error {self.mod_id}: {e}")

    def get_display_info(self, lang_code):
        """
        根据传入的语言代码 (cn/en) 返回 (name, desc)。
        如果对应语言为空，则回退到另一种语言，防止空白。
        """
        primary = lang_code
        secondary = 'en' if lang_code == 'cn' else 'cn'
        
        # 获取名字
        name = self.meta_data[primary]['name']
        if not name:
            name = self.meta_data[secondary]['name']
        if not name:
            name = self.mod_id # 都没有则显示ID

        # 获取描述
        desc = self.meta_data[primary]['desc']
        if not desc:
            desc = self.meta_data[secondary]['desc']
            
        return name, desc

# ==========================================
# 增强型 Treeview
# ==========================================
class ReorderableTreeview(ttk.Treeview):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_drop)
        self.drag_start_item = None
        self.separator = None 

    def create_separator(self):
        if not self.separator:
            self.separator = tk.Frame(self, height=2, bg="red")

    def on_click(self, event):
        self.create_separator()
        item = self.identify_row(event.y)
        if item:
            self.drag_start_item = item
            self.event_generate("<<TreeviewSelect>>")

    def on_drag(self, event):
        if not self.drag_start_item: return
        target_item = self.identify_row(event.y)
        if target_item:
            bbox = self.bbox(target_item)
            if bbox:
                self.separator.place(x=0, y=bbox[1], relwidth=1.0, height=2)
                self.separator.lift()
        else:
            self.separator.place_forget()

    def on_drop(self, event):
        self.separator.place_forget()
        target_item = self.identify_row(event.y)
        if not self.drag_start_item or not target_item: return
        if self.drag_start_item == target_item: return
        
        dst_index = self.index(target_item)
        self.move(self.drag_start_item, '', dst_index)
        self.drag_start_item = None

# ==========================================
# 主应用程序
# ==========================================

class ModManagerApp:
    def __init__(self, root):
        self.root = root
        self.current_lang = "cn" 
        self.ui_text = UI_LANG_DATA[self.current_lang]
        
        self.root.title(self.ui_text["title"])
        self.root.geometry("1200x850")

        self.app_dir = get_app_path()
        self.config_json_path = os.path.join(self.app_dir, APP_CONFIG_FILE)
        self.preset_root = os.path.join(self.app_dir, PRESET_DIR)

        self.config_path = tk.StringVar()
        self.mod_root_path = tk.StringVar()
        self.font_size = tk.IntVar(value=10)
        self.selected_lang_var = tk.StringVar(value="中文")
        
        self.mod_list = []
        self.config_parser = None
        
        self.main_font = font.Font(family="Microsoft YaHei", size=10)
        self.bold_font = font.Font(family="Microsoft YaHei", size=10, weight="bold")

        self.load_app_config()
        self._init_ui()
        self.update_ui_text() 

        if self.config_path.get() and self.mod_root_path.get():
            self.load_data(silent=True)

    def _init_ui(self):
        style = ttk.Style()
        style.configure("Treeview", font=self.main_font)
        style.configure("Treeview.Heading", font=self.bold_font)

        # --- Top Frame ---
        self.top_frame = tk.LabelFrame(self.root, padx=10, pady=10)
        self.top_frame.pack(fill="x", padx=10, pady=5)

        self.lbl_cfg = tk.Label(self.top_frame, font=self.main_font)
        self.lbl_cfg.grid(row=0, column=0, sticky="e")
        tk.Entry(self.top_frame, textvariable=self.config_path, width=60, font=self.main_font).grid(row=0, column=1, padx=5)
        self.btn_browse_cfg = tk.Button(self.top_frame, command=self.browse_config, font=self.main_font)
        self.btn_browse_cfg.grid(row=0, column=2)

        self.lbl_mod = tk.Label(self.top_frame, font=self.main_font)
        self.lbl_mod.grid(row=1, column=0, sticky="e")
        tk.Entry(self.top_frame, textvariable=self.mod_root_path, width=60, font=self.main_font).grid(row=1, column=1, padx=5)
        self.btn_browse_mod = tk.Button(self.top_frame, command=self.browse_mod_dir, font=self.main_font)
        self.btn_browse_mod.grid(row=1, column=2)

        # Button Frame
        btn_frame = tk.Frame(self.top_frame)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=10, sticky="w")
        
        self.btn_load = tk.Button(btn_frame, command=lambda: self.load_data(False), bg="#e1f5fe", font=self.bold_font)
        self.btn_load.pack(side="left", padx=5)
        
        self.btn_save = tk.Button(btn_frame, command=self.save_game_config, bg="#a5d6a7", font=self.bold_font)
        self.btn_save.pack(side="left", padx=5)

        # Settings
        tk.Label(btn_frame, text="|").pack(side="left", padx=5)
        self.lbl_font = tk.Label(btn_frame, font=self.main_font)
        self.lbl_font.pack(side="left")
        tk.Spinbox(btn_frame, from_=8, to=30, textvariable=self.font_size, width=3, command=self.update_font, font=self.main_font).pack(side="left")

        tk.Label(btn_frame, text="|").pack(side="left", padx=5)
        self.lbl_lang = tk.Label(btn_frame, font=self.main_font)
        self.lbl_lang.pack(side="left")
        
        lang_cb = ttk.Combobox(btn_frame, textvariable=self.selected_lang_var, values=["中文", "English"], width=8, state="readonly", font=self.main_font)
        lang_cb.pack(side="left")
        lang_cb.bind("<<ComboboxSelected>>", self.change_language)

        self.btn_save_preset = tk.Button(btn_frame, command=self.save_preset, font=self.main_font)
        self.btn_save_preset.pack(side="right", padx=5)
        self.btn_load_preset = tk.Button(btn_frame, command=self.load_preset, font=self.main_font)
        self.btn_load_preset.pack(side="right", padx=5)

        # --- Mid Frame ---
        mid_frame = tk.Frame(self.root)
        mid_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.list_frame = tk.LabelFrame(mid_frame)
        self.list_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.tree = ReorderableTreeview(self.list_frame, columns=("enabled", "name", "id"), show="headings", selectmode="browse")
        self.tree.column("enabled", width=80, anchor="center")
        self.tree.column("name", width=300)
        self.tree.column("id", width=100)
        
        sc = ttk.Scrollbar(self.list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sc.set)
        sc.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.bind("<Double-1>", self.toggle_mod)
        self.tree.bind("<<TreeviewSelect>>", self.show_details)

        self.detail_frame = tk.LabelFrame(mid_frame, width=400)
        self.detail_frame.pack(side="right", fill="both", padx=(5, 0))
        self.detail_frame.pack_propagate(False)

        self.img_label = tk.Label(self.detail_frame, bg="#eeeeee")
        self.img_label.pack(fill="x", padx=5, pady=5, ipady=20)

        self.lbl_mod_name = tk.Label(self.detail_frame, font=self.bold_font, wraplength=380)
        self.lbl_mod_name.pack(pady=5)

        self.txt_desc = tk.Text(self.detail_frame, wrap="word", font=self.main_font, bg="#f9f9f9", bd=0)
        self.txt_desc.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.update_font()

    # ================= UI Logic =================

    def update_ui_text(self):
        l = self.ui_text
        self.root.title(l["title"])
        self.top_frame.config(text=l["path_settings"])
        self.lbl_cfg.config(text=l["game_config"])
        self.lbl_mod.config(text=l["mod_dir"])
        self.btn_browse_cfg.config(text=l["browse"])
        self.btn_browse_mod.config(text=l["browse"])
        self.btn_load.config(text=l["load_refresh"])
        self.btn_save.config(text=l["save_config"])
        self.lbl_font.config(text=l["font_size"])
        self.lbl_lang.config(text=l["language"])
        self.btn_save_preset.config(text=l["save_preset"])
        self.btn_load_preset.config(text=l["load_preset"])
        
        self.list_frame.config(text=l["mod_list_title"])
        self.tree.heading("enabled", text=l["col_status"])
        self.tree.heading("name", text=l["col_name"])
        self.tree.heading("id", text=l["col_id"])
        
        self.detail_frame.config(text=l["mod_details"])
        self.img_label.config(text=l["no_image"])
        
        # 刷新内容以适应新语言
        self.refresh_list()
        # 如果有选中的模组，刷新详情
        sel = self.tree.selection()
        if sel:
            self.show_details(None)

    def change_language(self, event):
        sel = self.selected_lang_var.get()
        self.current_lang = "cn" if sel == "中文" else "en"
        self.ui_text = UI_LANG_DATA[self.current_lang]
        self.update_ui_text()
        self.save_app_config()

    def update_font(self):
        s = self.font_size.get()
        self.main_font.configure(size=s)
        self.bold_font.configure(size=s, weight="bold")
        ttk.Style().configure("Treeview", rowheight=int(s * 2.5))

    def load_app_config(self):
        if os.path.exists(self.config_json_path):
            try:
                with open(self.config_json_path, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                    self.config_path.set(d.get("config_path", ""))
                    self.mod_root_path.set(d.get("mod_root_path", ""))
                    self.font_size.set(d.get("font_size", 10))
                    self.current_lang = d.get("lang", "cn")
                    self.selected_lang_var.set("中文" if self.current_lang == "cn" else "English")
                    self.ui_text = UI_LANG_DATA[self.current_lang]
            except: pass

    def save_app_config(self):
        d = {
            "config_path": self.config_path.get(),
            "mod_root_path": self.mod_root_path.get(),
            "font_size": self.font_size.get(),
            "lang": self.current_lang
        }
        with open(self.config_json_path, 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=4)

    def browse_config(self):
        f = filedialog.askopenfilename(filetypes=[("INI/TXT", "*.ini *.txt")])
        if f:
            self.config_path.set(f)
            self.save_app_config()

    def browse_mod_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.mod_root_path.set(d)
            self.save_app_config()

    # ================= Core Logic =================

    def load_data(self, silent=False):
        cp = self.config_path.get()
        mp = self.mod_root_path.get()
        
        if not os.path.exists(cp) or not os.path.exists(mp):
            if not silent: messagebox.showerror(self.ui_text["msg_error"], self.ui_text["msg_path_err"])
            return

        self.config_parser = configparser.ConfigParser()
        self.config_parser.optionxform = str
        try:
            self.config_parser.read(cp, encoding='utf-8')
        except Exception as e:
            if not silent: messagebox.showerror("Error", str(e))
            return

        if 'LoadOrder' not in self.config_parser: return

        lo = self.config_parser['LoadOrder']
        tmp = []
        pat = re.compile(r'Mod(\d+)Directory', re.IGNORECASE)

        for k in lo.keys():
            m = pat.match(k)
            if m:
                idx = int(m.group(1))
                val = lo[k]
                if ',' in val:
                    mid = val.split(',')[0].strip()
                    en = val.split(',')[1].strip().lower() == 'true'
                    tmp.append((idx, ModItem(mid, en)))

        tmp.sort(key=lambda x: x[0])
        self.mod_list = [x[1] for x in tmp]

        # 加载详情
        for m in self.mod_list:
            m.load_info(mp)

        self.refresh_list()
        if not silent:
            messagebox.showinfo(self.ui_text["msg_success"], self.ui_text["msg_load_ok"].format(len(self.mod_list)))

    def refresh_list(self):
        """刷新 Treeview，根据当前语言显示对应的名字"""
        # 保留当前滚动位置和选中项（如果可能）
        sel = self.tree.selection()
        
        self.tree.delete(*self.tree.get_children())
        
        for m in self.mod_list:
            s = self.ui_text["status_on"] if m.enabled else self.ui_text["status_off"]
            # 核心修改：获取对应语言的名字
            d_name, _ = m.get_display_info(self.current_lang)
            
            item = self.tree.insert("", "end", values=(s, d_name, m.mod_id))
            
            # 恢复选中（通过 ID 匹配）
            if sel and self.mod_list.index(m) == 0: # 简单处理，暂不恢复复杂选中
                pass

    def toggle_mod(self, event):
        r = self.tree.identify_row(event.y)
        if not r: return
        idx = self.tree.index(r)
        m = self.mod_list[idx]
        m.enabled = not m.enabled
        s = self.ui_text["status_on"] if m.enabled else self.ui_text["status_off"]
        self.tree.set(r, "enabled", s)

    def show_details(self, event):
        sel = self.tree.selection()
        if not sel: return
        idx = self.tree.index(sel[0])
        m = self.mod_list[idx]
        
        # 核心修改：获取对应语言的名字和简介
        d_name, d_desc = m.get_display_info(self.current_lang)
        if not d_desc:
            d_desc = self.ui_text["fallback_desc"]

        self.lbl_mod_name.config(text=d_name)
        self.txt_desc.delete(1.0, "end")
        self.txt_desc.insert("end", d_desc)
        
        # 图片逻辑不变
        if m.image_path:
            try:
                img = Image.open(m.image_path)
                bw = 380
                wp = (bw / float(img.size[0]))
                hs = int((float(img.size[1]) * float(wp)))
                if hs > 300:
                    hs = 300
                    wp = (hs / float(img.size[1]))
                    bw = int((float(img.size[0]) * float(wp)))
                img = img.resize((bw, hs), Image.Resampling.LANCZOS)
                ti = ImageTk.PhotoImage(img)
                self.img_label.config(image=ti, text="")
                self.img_label.image = ti
            except:
                self.img_label.config(image="", text="Img Error")
        else:
            self.img_label.config(image="", text=self.ui_text["no_image"])

    def save_game_config(self):
        if not self.mod_list: return
        
        # 同步 Treeview 顺序
        cur_items = self.tree.get_children()
        new_list = []
        map_mod = {m.mod_id: m for m in self.mod_list}
        for it in cur_items:
            mid = self.tree.item(it, 'values')[2]
            if mid in map_mod: new_list.append(map_mod[mid])
        self.mod_list = new_list

        # 覆盖备份
        f_path = self.config_path.get()
        bak_path = f_path + ".bak"
        try:
            shutil.copy2(f_path, bak_path)
        except Exception as e:
            if not messagebox.askyesno(self.ui_text["msg_error"], self.ui_text["msg_backup_fail"].format(e)):
                return

        sec = self.config_parser['LoadOrder']
        to_del = [k for k in sec.keys() if 'directory' in k.lower() and k.lower().startswith('mod')]
        for k in to_del: del sec[k]
        
        for i, m in enumerate(self.mod_list):
            sec[f"Mod{i+1}Directory"] = f"{m.mod_id},{str(m.enabled)}"
        sec['NumberOfModFiles'] = str(len(self.mod_list))

        with open(f_path, 'w', encoding='utf-8') as f:
            self.config_parser.write(f)
        
        messagebox.showinfo(self.ui_text["msg_success"], self.ui_text["msg_saved"])

    def save_preset(self):
        if not os.path.exists(self.preset_root): os.makedirs(self.preset_root)
        fn = filedialog.asksaveasfilename(initialdir=self.preset_root, filetypes=[("JSON", "*.json")], defaultextension=".json")
        if not fn: return
        
        data = []
        cur_items = self.tree.get_children()
        map_mod = {m.mod_id: m for m in self.mod_list}
        for it in cur_items:
            mid = self.tree.item(it, 'values')[2]
            if mid in map_mod:
                m = map_mod[mid]
                # 预设里只存 ID 和当前显示的名字（方便人看），加载时只认ID
                d_name, _ = m.get_display_info("cn") 
                data.append({"id": m.mod_id, "n": d_name, "e": m.enabled})
        
        with open(fn, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        messagebox.showinfo(self.ui_text["msg_success"], self.ui_text["msg_preset_saved"])

    def load_preset(self):
        if not os.path.exists(self.preset_root): os.makedirs(self.preset_root)
        fn = filedialog.askopenfilename(initialdir=self.preset_root, filetypes=[("JSON", "*.json")])
        if not fn: return
        
        with open(fn, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        cur_map = {m.mod_id: m for m in self.mod_list}
        new_list = []
        missing = []
        
        for p in data:
            mid = p['id']
            if mid in cur_map:
                mod = cur_map[mid]
                mod.enabled = p['e']
                new_list.append(mod)
                del cur_map[mid]
            else:
                missing.append(f"{p.get('n', mid)} ({mid})")
                
        for m in cur_map.values():
            m.enabled = False
            new_list.append(m)
            
        self.mod_list = new_list
        self.refresh_list()
        
        msg = self.ui_text["msg_preset_loaded"]
        if missing:
            msg += self.ui_text["msg_preset_missing"] + "\n".join(missing[:10])
        messagebox.showinfo(self.ui_text["msg_success"], msg)

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1) 
    except: pass
    app = ModManagerApp(root)
    root.mainloop()