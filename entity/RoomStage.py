import tkinter as tk
from tkinter import messagebox
import json
import os

class EscapeGame3D:
    def __init__(self, root):
        """
        ゲームの初期設定を行うコンストラクタです。
        """
        self.root = root
        self.root.title("疑似3D脱出ゲーム")
        self.root.geometry("600x550") # スロットボタン等の配置のため、縦幅を少し広げました
        self.root.resizable(False, False)

        # 【変更】 3つのセーブスロットのファイル名を定義
        self.SAVE_SLOTS = {
            1: "save_data_1.json",
            2: "save_data_2.json",
            3: "save_data_3.json"
        }

        # プレイヤーの所持品（インベントリ）を管理するリスト
        self.inventory = []
        
        # 現在「選択中」のアイテム名
        self.selected_item = None

        # 各視点の背景画像のファイル名やデータを定義
        self.room_data = {
            "北": {
                "image_file": "bg_north.png",
                "color": "#dcdcdc",
                "object": "【大きな鉄の扉】\n（鍵がかかっている）", 
                "next_left": "西", "next_right": "東",
                "item": None,
                "door": {"coords": (180, 80, 320, 260), "locked": True}
            },
            "東": {
                "image_file": "bg_east.png",
                "color": "#ffe4e1", 
                "object": "【引き出し付きの棚】\n（中には何もなさそうだ）", 
                "next_left": "北", "next_right": "南",
                "item": None
            },
            "南": {
                "image_file": "bg_south.png",
                "color": "#e0ffff", 
                "object": "【開かない窓】\n（外は暗くて何も見えない）", 
                "next_left": "東", "next_right": "西",
                "item": None
            },
            "西": {
                "image_file": "bg_west.png",
                "color": "#fafad2", 
                "object": "【机】\n（何かが置いてあるぞ…？）", 
                "next_left": "南", "next_right": "北",
                "item": {"name": "古い鍵", "coords": (220, 200, 280, 230), "picked": False}
            }
        }

        # 画像オブジェクトを保持するための辞書・変数
        self.bg_images = {}
        self.title_image = None
        self.load_all_images()

        # 最初は「北」からスタート
        self.current_direction = "北"

        # 画面を切り替えるためのベースフレーム
        self.title_frame = tk.Frame(self.root, width=600, height=550)
        self.game_frame = tk.Frame(self.root, width=600, height=550)

        # 画面の部品（UI）を作成
        self.create_title_widgets()
        self.create_game_widgets()
        
        # 最初はタイトル画面を表示する
        self.show_title_screen()

    def load_all_images(self):
        """背景画像およびタイトル画像を事前に読み込みます。"""
        for direction, data in self.room_data.items():
            file_path = data["image_file"]
            if os.path.exists(file_path):
                try:
                    self.bg_images[direction] = tk.PhotoImage(file=file_path)
                except Exception as e:
                    print(f"画像 {file_path} の読み込みに失敗しました: {e}")
                    self.bg_images[direction] = None
            else:
                self.bg_images[direction] = None

        title_file = "bg_title.png"
        if os.path.exists(title_file):
            try:
                self.title_image = tk.PhotoImage(file=title_file)
            except Exception as e:
                print(f"タイトル画像の読み込みに失敗しました: {e}")
                self.title_image = None

    def create_title_widgets(self):
        """
        【変更】 タイトル画面のレイアウトを構築します（ロードスロットを追加）。
        """
        self.title_canvas = tk.Canvas(self.title_frame, width=600, height=550, bg="#e0f7fa", highlightthickness=0)
        self.title_canvas.pack()

        if self.title_image:
            self.title_canvas.create_image(300, 275, image=self.title_image)

        # ゲームタイトル文字
        self.title_canvas.create_text(
            300, 100, 
            text="長崎大学脱出ゲーム\n- 閉ざされた学び舎 -", 
            font=("MS Gothic", 26, "bold"), 
            fill="#006064", 
            justify="center"
        )

        # --- はじめからスタートするボタン ---
        btn_start = tk.Button(
            self.title_frame, text="NEW GAME (新しく始める)", font=("MS Gothic", 12, "bold"),
            bg="#00838f", fg="white", activebackground="#005662", activeforeground="white",
            command=self.start_new_game, width=22, height=2, relief="raised", bd=3
        )
        self.title_canvas.create_window(300, 200, window=btn_start)

        # --- 【追加】 セーブデータ選択（ロード）エリアのラベル ---
        self.title_canvas.create_text(
            300, 270, 
            text="▼ 続きから始める（スロットを選択） ▼", 
            font=("MS Gothic", 11, "bold"), 
            fill="#004d40"
        )

        # 【追加】 タイトル表示用に、各スロットのボタンを保持するリスト
        self.slot_buttons = []
        
        # スロット1〜3のボタンを縦に並べて配置する処理
        for slot_num in [1, 2, 3]:
            btn = tk.Button(
                self.title_frame, text="", font=("MS Gothic", 10),
                bg="#f5f5f5", relief="raised", bd=2, width=45, anchor="w", padx=10,
                command=lambda s=slot_num: self.load_game(s)
            )
            self.slot_buttons.append(btn)
            # キャンバス内にボタンを配置 (Y座標をずらしながら配置します)
            self.title_canvas.create_window(300, 310 + (slot_num - 1) * 45, window=btn)

        # クレジット表記
        self.title_canvas.create_text(
            300, 520, 
            text="© 2026 Soshiro Nishimura", 
            font=("MS Gothic", 10), 
            fill="#555555"
        )

    def create_game_widgets(self):
        """ゲーム本編の画面レイアウトを構築します。"""
        self.direction_label = tk.Label(self.game_frame, text="", font=("MS Gothic", 16, "bold"))
        self.direction_label.pack(pady=5)

        self.canvas = tk.Canvas(self.game_frame, width=500, height=300, bg="white", relief="ridge", bd=2)
        self.canvas.pack(pady=5)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        self.inventory_frame = tk.Frame(self.game_frame)
        self.inventory_frame.pack(pady=5)
        
        self.select_status_label = tk.Label(self.game_frame, text="選択中: なし", font=("MS Gothic", 10), fg="darkgreen")
        self.select_status_label.pack(pady=2)

        # 最下部：操作ボタン
        button_frame = tk.Frame(self.game_frame)
        button_frame.pack(fill="x", pady=5)

        self.btn_left = tk.Button(button_frame, text="◀ 左を向く", font=("MS Gothic", 12), command=self.turn_left, width=12, height=2)
        self.btn_left.pack(side="left", padx=50)

        self.btn_investigate = tk.Button(button_frame, text="🔍 調べる", font=("MS Gothic", 12), command=self.investigate, width=12, height=2)
        self.btn_investigate.pack(side="left", padx=20)

        self.btn_right = tk.Button(button_frame, text="右を向く ▶", font=("MS Gothic", 12), command=self.turn_right, width=12, height=2)
        self.btn_right.pack(side="right", padx=50)

        # 【変更】 セーブボタンエリア（3つのスロットに保存できるようボタンを3つ並べます）
        system_frame = tk.Frame(self.game_frame)
        system_frame.pack(pady=5)

        tk.Label(system_frame, text="💾 セーブ保存先: ", font=("MS Gothic", 10, "bold")).pack(side="left", padx=5)
        for slot_num in [1, 2, 3]:
            btn_save = tk.Button(
                system_frame, text=f"スロット {slot_num}", font=("MS Gothic", 9, "bold"),
                command=lambda s=slot_num: self.save_game(s), bg="#e1f5fe", width=10
            )
            btn_save.pack(side="left", padx=5)

        # タイトルに戻るボタン
        btn_back_title = tk.Button(
            system_frame, text="↩ タイトルへ", font=("MS Gothic", 9),
            command=self.show_title_screen, bg="#ffe0b2", width=10
        )
        btn_back_title.pack(side="left", padx=20)

    def show_title_screen(self):
        """【変更】 タイトル画面を表示します。その際、セーブデータの状態を確認してボタン文字を更新します。"""
        self.game_frame.pack_forget()
        self.title_frame.pack(fill="both", expand=True)
        self.update_title_slot_buttons() # スロット表示を最新にする

    def update_title_slot_buttons(self):
        """
        【追加】 セーブファイルの有無を調べ、タイトル画面のロードボタンのテキストを更新します。
        """
        for slot_num, file_name in self.SAVE_SLOTS.items():
            btn = self.slot_buttons[slot_num - 1]
            if os.path.exists(file_name):
                try:
                    with open(file_name, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # セーブデータの内容（向きやアイテム数）をボタンに少し表示して分かりやすくします
                    item_count = len(data["inventory"])
                    direction = data["current_direction"]
                    btn.config(
                        text=f" スロット {slot_num} : 【{direction}の壁】に滞在中 (アイテム: {item_count}個)", 
                        state="normal", bg="#e8f5e9"
                    )
                except:
                    btn.config(text=f" スロット {slot_num} : データ破損エラー", state="disabled", bg="#ffebee")
            else:
                # データがない場合はクリックできないようにします
                btn.config(text=f" スロット {slot_num} : ---------- NO DATA ----------", state="disabled", bg="#f5f5f5")

    def start_new_game(self):
        """【追加】 「はじめから」ゲームをリセットして開始します。"""
        self.inventory = []
        self.selected_item = None
        self.current_direction = "北"
        self.room_data["西"]["item"]["picked"] = False
        self.room_data["北"]["door"]["locked"] = True
        self.room_data["北"]["object"] = "【大きな鉄の扉】\n（鍵がかかっている）"
        
        self.title_frame.pack_forget()
        self.game_frame.pack(fill="both", expand=True)
        self.update_screen()

    def start_game_loaded(self):
        """ロード成功後にゲーム画面に切り替えます。"""
        self.title_frame.pack_forget()
        self.game_frame.pack(fill="both", expand=True)
        self.update_screen()

    def update_screen(self):
        """現在の状態に基づいて、ゲーム画面を再描画します。"""
        data = self.room_data[self.current_direction]
        self.direction_label.config(text=f"【 {self.current_direction} の壁 】")
        
        self.canvas.delete("all")
        
        if self.bg_images[self.current_direction]:
            self.canvas.create_image(250, 150, image=self.bg_images[self.current_direction])
        else:
            self.canvas.create_rectangle(0, 0, 500, 300, fill=data["color"], outline="")
        
        if self.current_direction == "北" and "door" in data:
            dc = data["door"]["coords"]
            if not self.bg_images[self.current_direction]:
                self.canvas.create_rectangle(dc[0], dc[1], dc[2], dc[3], fill="#8b4513", outline="#5c2e0b", width=3)
                self.canvas.create_oval(dc[2]-20, (dc[1]+dc[3])//2-5, dc[2]-10, (dc[1]+dc[3])//2+5, fill="gold")

        self.canvas.create_text(250, 50, text=data["object"], font=("MS Gothic", 14, "bold"), justify="center")

        if data["item"] and not data["item"]["picked"]:
            coords = data["item"]["coords"]
            self.canvas.create_oval(coords[0], coords[1], coords[0]+20, coords[1]+20, fill="gold", outline="orange")
            self.canvas.create_rectangle(coords[0]+15, coords[1]+7, coords[2], coords[1]+13, fill="gold", outline="orange")
            self.canvas.create_text(coords[0]+30, coords[1]+25, text=data["item"]["name"], font=("MS Gothic", 9, "bold"))

        # インベントリボタンの更新
        for widget in self.inventory_frame.winfo_children():
            widget.destroy()
            
        tk.Label(self.inventory_frame, text="所持品: ", font=("MS Gothic", 11)).pack(side="left")
        
        if not self.inventory:
            tk.Label(self.inventory_frame, text="なし", font=("MS Gothic", 11), fg="gray").pack(side="left")
        else:
            for item_name in self.inventory:
                btn = tk.Button(self.inventory_frame, text=item_name, font=("MS Gothic", 10),
                                command=lambda name=item_name: self.select_item(name), relief="raised", bd=2)
                if item_name == self.selected_item:
                    btn.config(relief="sunken", bg="lightgreen")
                btn.pack(side="left", padx=5)

        if self.selected_item:
            self.select_status_label.config(text=f"選択中: [ {self.selected_item} ] (この状態で対象をクリック！)")
        else:
            self.select_status_label.config(text="選択中: なし")

    def select_item(self, item_name):
        """アイテム欄のボタンが押されたとき、そのアイテムを選択状態にします。"""
        if self.selected_item == item_name:
            self.selected_item = None
        else:
            self.selected_item = item_name
        self.update_screen()

    def on_canvas_click(self, event):
        """キャンバス内がクリックされたときの処理です。"""
        click_x = event.x
        click_y = event.y
        data = self.room_data[self.current_direction]
        
        # 扉のクリック判定
        if self.current_direction == "北" and "door" in data:
            dc = data["door"]["coords"]
            if dc[0] <= click_x <= dc[2] and dc[1] <= click_y <= dc[3]:
                if data["door"]["locked"] and self.selected_item == "古い鍵":
                    data["door"]["locked"] = False
                    data["object"] = "【大きな鉄の扉】\n（鍵が開いた！脱出できるぞ！）"
                    self.inventory.remove("古い鍵")
                    self.selected_item = None
                    messagebox.showinfo("カチャリ…", "古い鍵を使って扉のロックを解除した！")
                    self.update_screen()
                    return
                elif not data["door"]["locked"]:
                    messagebox.showinfo("クリア！", "おめでとうございます！\n部屋から脱出しました！")
                    self.show_title_screen()
                    return
                else:
                    messagebox.showwarning("調べた", "扉には頑丈な鍵がかかっていて開かない。")
                    return

        # アイテムのクリック判定
        if data["item"] and not data["item"]["picked"]:
            item = data["item"]
            x1, y1, x2, y2 = item["coords"]
            if (x1 - 10) <= click_x <= (x2 + 10) and (y1 - 10) <= click_y <= (y2 + 10):
                item["picked"] = True
                self.inventory.append(item["name"])
                messagebox.showinfo("アイテムゲット", f"「{item['name']}」を拾った！")
                self.update_screen()

    def turn_left(self):
        """視点を左に切り替えます。"""
        current_data = self.room_data[self.current_direction]
        self.current_direction = current_data["next_left"]
        self.update_screen()

    def turn_right(self):
        """視点を右に切り替えます。"""
        current_data = self.room_data[self.current_direction]
        self.current_direction = current_data["next_right"]
        self.update_screen()

    def investigate(self):
        """中央のオブジェクトを調べた時の処理です。"""
        data = self.room_data[self.current_direction]
        messagebox.showinfo("調べる", data["object"].replace('\n', ''))

    # ==========================================================================
    # 【変更】 セーブ＆ロード処理（スロット番号を受け取るように拡張）
    # ==========================================================================
    def save_game(self, slot_num):
        """
        指定されたスロット番号に現在のゲーム状態を保存します。
        """
        file_name = self.SAVE_SLOTS[slot_num]
        
        save_data = {
            "current_direction": self.current_direction,
            "inventory": self.inventory,
            "key_picked": self.room_data["西"]["item"]["picked"],
            "door_locked": self.room_data["北"]["door"]["locked"],
            "north_object": self.room_data["北"]["object"]
        }
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("セーブ完了", f"スロット {slot_num} にゲームの状態を保存しました！")
        except Exception as e:
            messagebox.showerror("エラー", f"セーブに失敗しました:\n{e}")

    def load_game(self, slot_num):
        """
        指定されたスロット番号のJSONファイルからゲーム状態を読み込んで復元します。
        """
        file_name = self.SAVE_SLOTS[slot_num]
        
        if not os.path.exists(file_name):
            messagebox.showwarning("ロード失敗", f"スロット {slot_num} のセーブデータが見つかりません。")
            return
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                save_data = json.load(f)

            self.current_direction = save_data["current_direction"]
            self.inventory = save_data["inventory"]
            self.room_data["西"]["item"]["picked"] = save_data["key_picked"]
            self.room_data["北"]["door"]["locked"] = save_data["door_locked"]
            self.room_data["北"]["object"] = save_data["north_object"]
            self.selected_item = None
            
            # ロード成功したら本編画面へ切り替え
            self.start_game_loaded()
            messagebox.showinfo("ロード完了", f"スロット {slot_num} からゲームを再開します！")
        except Exception as e:
            messagebox.showerror("エラー", f"ロードに失敗しました:\n{e}")

# ==============================================================================
# プログラムの実行
# ==============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    game = EscapeGame3D(root)
    root.mainloop()