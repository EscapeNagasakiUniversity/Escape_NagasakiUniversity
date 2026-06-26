import tkinter as tk
from tkinter import messagebox

class EscapeGame3D:
    def __init__(self, root):
        """
        ゲームの初期設定を行うコンストラクタです。
        """
        self.root = root
        self.root.title("疑似3D脱出ゲーム")
        self.root.geometry("600x480") # 下部に選択状態を表示するため、少し縦幅を広げました
        self.root.resizable(False, False)

        # プレイヤーの所持品（インベントリ）を管理するリスト
        self.inventory = []
        
        # 【追加】 現在「選択中」のアイテム名を保持する変数（Noneは何も選択していない状態）
        self.selected_item = None

        # 1. 各「視点（方向）」のデータを定義
        # 【変更】 北の壁に、クリックできる「扉」の判定座標(coords)と状態(locked)を追加しました。
        self.room_data = {
            "北": {
                "color": "#dcdcdc", 
                "object": "【大きな鉄の扉】\n（鍵がかかっている）", 
                "next_left": "西", "next_right": "東",
                "item": None,
                # 扉のクリック判定用の座標（中央付近）と、鍵がかかっているかどうかのフラグ
                "door": {"coords": (180, 80, 320, 260), "locked": True}
            },
            "東": {
                "color": "#ffe4e1", 
                "object": "【引き出し付きの棚】\n（中には何もなさそうだ）", 
                "next_left": "北", "next_right": "南",
                "item": None
            },
            "南": {
                "color": "#e0ffff", 
                "object": "【開かない窓】\n（外は暗くて何も見えない）", 
                "next_left": "東", "next_right": "西",
                "item": None
            },
            "西": {
                "color": "#fafad2", 
                "object": "【机】\n（何かが置いてあるぞ…？）", 
                "next_left": "南", "next_right": "北",
                "item": {"name": "古い鍵", "coords": (220, 200, 280, 230), "picked": False}
            }
        }

        # 2. 最初は「北」からスタート
        self.current_direction = "北"

        # 3. 画面のレイアウト（UI）を構築
        self.create_widgets()
        
        # 4. 初回の画面描画
        self.update_screen()

    def create_widgets(self):
        """
        画面を構成するボタンやキャンバス（画像表示エリア）を作成します。
        """
        # --- 上部：現在の方向を表示するラベル ---
        self.direction_label = tk.Label(self.root, text="", font=("MS Gothic", 16, "bold"))
        self.direction_label.pack(pady=5)

        # --- 中央：メインの景色を描画するキャンバス ---
        self.canvas = tk.Canvas(self.root, width=500, height=300, bg="white", relief="ridge", bd=2)
        self.canvas.pack(pady=5)

        # キャンバス内がクリックされたときに、on_canvas_click 関数を呼び出す
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # --- 下部：所持品（インベントリ）を表示するフレーム ---
        # 【変更】 アイテムをクリックして選択できるようにするため、ボタンを並べる形式に変更します
        self.inventory_frame = tk.Frame(self.root)
        self.inventory_frame.pack(pady=5)
        
        # 【追加】 現在どのアイテムを選択しているかを表示するラベル
        self.select_status_label = tk.Label(self.root, text="選択中: なし", font=("MS Gothic", 10), fg="darkgreen")
        self.select_status_label.pack(pady=2)

        # --- 最下部：操作ボタンを配置するフレーム ---
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill="x", pady=5)

        # 左を向くボタン
        self.btn_left = tk.Button(button_frame, text="◀ 左を向く", font=("MS Gothic", 12),
                                  command=self.turn_left, width=12, height=2)
        self.btn_left.pack(side="left", padx=50)

        # 調べるボタン
        self.btn_investigate = tk.Button(button_frame, text="🔍 調べる", font=("MS Gothic", 12),
                                         command=self.investigate, width=12, height=2)
        self.btn_investigate.pack(side="left", padx=20)

        # 右を向くボタン
        self.btn_right = tk.Button(button_frame, text="右を向く ▶", font=("MS Gothic", 12),
                                   command=self.turn_right, width=12, height=2)
        self.btn_right.pack(side="right", padx=50)

    def update_screen(self):
        """
        現在の方向に基づいて、画面の画像（景色）、アイテム、インベントリボタンを更新します。
        """
        data = self.room_data[self.current_direction]
        self.direction_label.config(text=f"【 {self.current_direction} の壁 】")
        
        # キャンバスをクリア
        self.canvas.delete("all")
        
        # 背景（壁）を描画
        self.canvas.create_rectangle(0, 0, 500, 300, fill=data["color"], outline="")
        
        # 【追加】 北の壁の場合、扉のグラフィック（茶色の四角）を描画
        if self.current_direction == "北" and "door" in data:
            dc = data["door"]["coords"]
            self.canvas.create_rectangle(dc[0], dc[1], dc[2], dc[3], fill="#8b4513", outline="#5c2e0b", width=3)
            # ドアノブ
            self.canvas.create_oval(dc[2]-20, (dc[1]+dc[3])//2-5, dc[2]-10, (dc[1]+dc[3])//2+5, fill="gold")

        # 中央のオブジェクトテキストを描画（少し位置を調整）
        self.canvas.create_text(250, 50, text=data["object"], font=("MS Gothic", 14, "bold"), justify="center")

        # アイテムの描画処理（西の壁）
        if data["item"] and not data["item"]["picked"]:
            coords = data["item"]["coords"]
            self.canvas.create_oval(coords[0], coords[1], coords[0]+20, coords[1]+20, fill="gold", outline="orange")
            self.canvas.create_rectangle(coords[0]+15, coords[1]+7, coords[2], coords[1]+13, fill="gold", outline="orange")
            self.canvas.create_text(coords[0]+30, coords[1]+25, text=data["item"]["name"], font=("MS Gothic", 9, "bold"))

        # 【変更】 インベントリ（アイテム欄）のボタン表示を更新
        # 一度古いボタンをすべて削除します
        for widget in self.inventory_frame.winfo_children():
            widget.destroy()
            
        tk.Label(self.inventory_frame, text="所持品: ", font=("MS Gothic", 11)).pack(side="left")
        
        if not self.inventory:
            tk.Label(self.inventory_frame, text="なし", font=("MS Gothic", 11), fg="gray").pack(side="left")
        else:
            # 拾ったアイテムを1つずつボタンとして並べます
            for item_name in self.inventory:
                # クリックされたら select_item(item_name) が実行されるようにします
                btn = tk.Button(self.inventory_frame, text=item_name, font=("MS Gothic", 10),
                                command=lambda name=item_name: self.select_item(name), relief="raised", bd=2)
                
                # もしそのアイテムが現在選択中なら、ボタンの色を沈ませて分かりやすくします
                if item_name == self.selected_item:
                    btn.config(relief="sunken", bg="lightgreen")
                    
                btn.pack(side="left", padx=5)

        # 選択状態ラベルの更新
        if self.selected_item:
            self.select_status_label.config(text=f"選択中: [ {self.selected_item} ] (この状態で対象をクリック！)")
        else:
            self.select_status_label.config(text="選択中: なし")

    def select_item(self, item_name):
        """
        【追加】 アイテム欄のボタンが押されたとき、そのアイテムを選択状態（または解除）にします。
        """
        if self.selected_item == item_name:
            self.selected_item = None # すでに選択されているものをもう一度押したら解除
        else:
            self.selected_item = item_name # 選択状態にする
            
        self.update_screen()

    def on_canvas_click(self, event):
        """
        キャンバス内がクリックされたときに実行される関数です。
        アイテムの取得、または扉に対して鍵を使う処理を行います。
        """
        click_x = event.x
        click_y = event.y
        data = self.room_data[self.current_direction]
        
        # --- 1. 北の壁で「扉」がクリックされたかどうかの判定 ---
        if self.current_direction == "北" and "door" in data:
            dc = data["door"]["coords"]
            if dc[0] <= click_x <= dc[2] and dc[1] <= click_y <= dc[3]:
                
                # 【鍵の使用処理】 扉がロックされていて、かつ「古い鍵」を選択している場合
                if data["door"]["locked"] and self.selected_item == "古い鍵":
                    data["door"]["locked"] = False
                    data["object"] = "【大きな鉄の扉】\n（鍵が開いた！脱出できるぞ！）"
                    self.inventory.remove("古い鍵") # 使ったのでインベントリから消去
                    self.selected_item = None
                    messagebox.showinfo("カチャリ…", "古い鍵を使って扉のロックを解除した！")
                    self.update_screen()
                    return
                
                # 鍵が開いた状態で、もう一度扉をクリックするとゲームクリア！
                elif not data["door"]["locked"]:
                    messagebox.showinfo("クリア！", "おめでとうございます！\n扉を開けて部屋から脱出しました！")
                    self.root.destroy() # ウィンドウを閉じてゲーム終了
                    return
                
                # 鍵を持っていない、または選択していない場合
                else:
                    messagebox.showwarning("調べた", "扉には頑丈な鍵がかかっていて開かない。")
                    return

        # --- 2. 西の壁で「アイテム」がクリックされたかどうかの判定 ---
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


# ==============================================================================
# プログラムの実行
# ==============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    game = EscapeGame3D(root)
    root.mainloop()