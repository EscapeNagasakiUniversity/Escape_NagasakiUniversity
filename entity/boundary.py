"""
boundary.py
-----------
Tkinterによる画面表示・ユーザー操作の受け付けを担当するboundaryレイヤー。
ロジック判断はcontrol.GameManagerに委譲し、ここでは
「画面の構築」「イベント受付」「結果の表示（メッセージボックス等）」のみを行う。
"""

import tkinter as tk
from tkinter import messagebox
import os

from control import GameManager


class EscapeGame3D:
    def __init__(self, root):
        """ゲームの初期設定を行うコンストラクタです。"""
        self.root = root
        self.root.title("疑似3D脱出ゲーム")
        self.root.geometry("600x550")
        self.root.resizable(False, False)

        # ロジック本体（controlレイヤー）
        self.manager = GameManager()

        # 画像オブジェクトを保持するための辞書・変数
        self.bg_images = {}
        self.title_image = None
        self.load_all_images()

        # 画面を切り替えるためのベースフレーム
        self.title_frame = tk.Frame(self.root, width=600, height=550)
        self.game_frame = tk.Frame(self.root, width=600, height=550)

        # 画面の部品（UI）を作成
        self.create_title_widgets()
        self.create_game_widgets()

        # 最初はタイトル画面を表示する
        self.show_title_screen()

    # ==================================================================
    # 画像読み込み
    # ==================================================================
    def load_all_images(self):
        """背景画像およびタイトル画像を事前に読み込みます。"""
        for direction, stage in self.manager.room_data.items():
            file_path = stage.image_file
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

    # ==================================================================
    # タイトル画面
    # ==================================================================
    def create_title_widgets(self):
        """タイトル画面のレイアウトを構築します（ロードスロットを含む）。"""
        self.title_canvas = tk.Canvas(self.title_frame, width=600, height=550, bg="#e0f7fa", highlightthickness=0)
        self.title_canvas.pack()

        if self.title_image:
            self.title_canvas.create_image(300, 275, image=self.title_image)

        self.title_canvas.create_text(
            300, 100,
            text="長崎大学脱出ゲーム\n- 閉ざされた学び舎 -",
            font=("MS Gothic", 26, "bold"),
            fill="#006064",
            justify="center"
        )

        btn_start = tk.Button(
            self.title_frame, text="NEW GAME (新しく始める)", font=("MS Gothic", 12, "bold"),
            bg="#00838f", fg="white", activebackground="#005662", activeforeground="white",
            command=self.start_new_game, width=22, height=2, relief="raised", bd=3
        )
        self.title_canvas.create_window(300, 200, window=btn_start)

        self.title_canvas.create_text(
            300, 270,
            text="▼ 続きから始める（スロットを選択） ▼",
            font=("MS Gothic", 11, "bold"),
            fill="#004d40"
        )

        self.slot_buttons = []
        for slot_num in [1, 2, 3]:
            btn = tk.Button(
                self.title_frame, text="", font=("MS Gothic", 10),
                bg="#f5f5f5", relief="raised", bd=2, width=45, anchor="w", padx=10,
                command=lambda s=slot_num: self.load_game(s)
            )
            self.slot_buttons.append(btn)
            self.title_canvas.create_window(300, 310 + (slot_num - 1) * 45, window=btn)

        self.title_canvas.create_text(
            300, 520,
            text="© 2026 Soshiro Nishimura",
            font=("MS Gothic", 10),
            fill="#555555"
        )

    # ==================================================================
    # ゲーム画面
    # ==================================================================
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

        button_frame = tk.Frame(self.game_frame)
        button_frame.pack(fill="x", pady=5)

        self.btn_left = tk.Button(button_frame, text="◀ 左を向く", font=("MS Gothic", 12), command=self.turn_left, width=12, height=2)
        self.btn_left.pack(side="left", padx=50)

        self.btn_investigate = tk.Button(button_frame, text="🔍 調べる", font=("MS Gothic", 12), command=self.investigate, width=12, height=2)
        self.btn_investigate.pack(side="left", padx=20)

        self.btn_right = tk.Button(button_frame, text="右を向く ▶", font=("MS Gothic", 12), command=self.turn_right, width=12, height=2)
        self.btn_right.pack(side="right", padx=50)

        system_frame = tk.Frame(self.game_frame)
        system_frame.pack(pady=5)

        tk.Label(system_frame, text="💾 セーブ保存先: ", font=("MS Gothic", 10, "bold")).pack(side="left", padx=5)
        for slot_num in [1, 2, 3]:
            btn_save = tk.Button(
                system_frame, text=f"スロット {slot_num}", font=("MS Gothic", 9, "bold"),
                command=lambda s=slot_num: self.save_game(s), bg="#e1f5fe", width=10
            )
            btn_save.pack(side="left", padx=5)

        btn_back_title = tk.Button(
            system_frame, text="↩ タイトルへ", font=("MS Gothic", 9),
            command=self.show_title_screen, bg="#ffe0b2", width=10
        )
        btn_back_title.pack(side="left", padx=20)

    def show_title_screen(self):
        """タイトル画面を表示し、セーブデータの状態を確認してボタン文字を更新します。"""
        self.game_frame.pack_forget()
        self.title_frame.pack(fill="both", expand=True)
        self.update_title_slot_buttons()

    def update_title_slot_buttons(self):
        """セーブファイルの有無を調べ、タイトル画面のロードボタンのテキストを更新します。"""
        for slot_num in [1, 2, 3]:
            btn = self.slot_buttons[slot_num - 1]
            summary = self.manager.get_slot_summary(slot_num)

            if summary["status"] == "ok":
                btn.config(
                    text=f" スロット {slot_num} : 【{summary['direction']}の壁】に滞在中 (アイテム: {summary['item_count']}個)",
                    state="normal", bg="#e8f5e9"
                )
            elif summary["status"] == "error":
                btn.config(text=f" スロット {slot_num} : データ破損エラー", state="disabled", bg="#ffebee")
            else:
                btn.config(text=f" スロット {slot_num} : ---------- NO DATA ----------", state="disabled", bg="#f5f5f5")

    # ==================================================================
    # 画面遷移
    # ==================================================================
    def start_new_game(self):
        """「はじめから」ゲームをリセットして開始します。"""
        self.manager.start_new_game()
        self.title_frame.pack_forget()
        self.game_frame.pack(fill="both", expand=True)
        self.update_screen()

    def start_game_loaded(self):
        """ロード成功後にゲーム画面に切り替えます。"""
        self.title_frame.pack_forget()
        self.game_frame.pack(fill="both", expand=True)
        self.update_screen()

    # ==================================================================
    # 画面描画
    # ==================================================================
    def update_screen(self):
        """現在の状態に基づいて、ゲーム画面を再描画します。"""
        player = self.manager.player
        data = self.manager.room_data[player.current_direction]
        self.direction_label.config(text=f"【 {player.current_direction} の壁 】")

        self.canvas.delete("all")

        if self.bg_images[player.current_direction]:
            self.canvas.create_image(250, 150, image=self.bg_images[player.current_direction])
        else:
            self.canvas.create_rectangle(0, 0, 500, 300, fill=data.color, outline="")

        if player.current_direction == "北" and data.door:
            dc = data.door.coords
            if not self.bg_images[player.current_direction]:
                self.canvas.create_rectangle(dc[0], dc[1], dc[2], dc[3], fill="#8b4513", outline="#5c2e0b", width=3)
                self.canvas.create_oval(dc[2] - 20, (dc[1] + dc[3]) // 2 - 5, dc[2] - 10, (dc[1] + dc[3]) // 2 + 5, fill="gold")

        self.canvas.create_text(250, 50, text=data.object_text, font=("MS Gothic", 14, "bold"), justify="center")

        if data.item and not data.item.picked:
            coords = data.item.coords
            self.canvas.create_oval(coords[0], coords[1], coords[0] + 20, coords[1] + 20, fill="gold", outline="orange")
            self.canvas.create_rectangle(coords[0] + 15, coords[1] + 7, coords[2], coords[1] + 13, fill="gold", outline="orange")
            self.canvas.create_text(coords[0] + 30, coords[1] + 25, text=data.item.name, font=("MS Gothic", 9, "bold"))

        # インベントリボタンの更新
        for widget in self.inventory_frame.winfo_children():
            widget.destroy()

        tk.Label(self.inventory_frame, text="所持品: ", font=("MS Gothic", 11)).pack(side="left")

        if not player.inventory:
            tk.Label(self.inventory_frame, text="なし", font=("MS Gothic", 11), fg="gray").pack(side="left")
        else:
            for item_name in player.inventory:
                btn = tk.Button(self.inventory_frame, text=item_name, font=("MS Gothic", 10),
                                 command=lambda name=item_name: self.select_item(name), relief="raised", bd=2)
                if item_name == player.selected_item:
                    btn.config(relief="sunken", bg="lightgreen")
                btn.pack(side="left", padx=5)

        if player.selected_item:
            self.select_status_label.config(text=f"選択中: [ {player.selected_item} ] (この状態で対象をクリック！)")
        else:
            self.select_status_label.config(text="選択中: なし")

    # ==================================================================
    # ユーザー操作 → controlへの委譲
    # ==================================================================
    def select_item(self, item_name):
        """アイテム欄のボタンが押されたとき、そのアイテムを選択状態にします。"""
        self.manager.select_item(item_name)
        self.update_screen()

    def on_canvas_click(self, event):
        """キャンバス内がクリックされたときの処理です。"""
        result = self.manager.object_identify(event.x, event.y)
        if result is None:
            return

        event_type, title, message = result

        if event_type == "unlock":
            messagebox.showinfo(title, message)
            self.update_screen()
        elif event_type == "clear":
            messagebox.showinfo(title, message)
            self.show_title_screen()
        elif event_type == "locked":
            messagebox.showwarning(title, message)
        elif event_type == "get_item":
            messagebox.showinfo(title, message)
            self.update_screen()

    def turn_left(self):
        """視点を左に切り替えます。"""
        self.manager.turn_left()
        self.update_screen()

    def turn_right(self):
        """視点を右に切り替えます。"""
        self.manager.turn_right()
        self.update_screen()

    def investigate(self):
        """中央のオブジェクトを調べた時の処理です。"""
        messagebox.showinfo("調べる", self.manager.get_investigate_text())

    # ==================================================================
    # セーブ／ロード
    # ==================================================================
    def save_game(self, slot_num):
        """指定されたスロット番号に現在のゲーム状態を保存します。"""
        try:
            self.manager.save_game(slot_num)
            messagebox.showinfo("セーブ完了", f"スロット {slot_num} にゲームの状態を保存しました！")
        except Exception as e:
            messagebox.showerror("エラー", f"セーブに失敗しました:\n{e}")

    def load_game(self, slot_num):
        """指定されたスロット番号のJSONファイルからゲーム状態を読み込んで復元します。"""
        if not self.manager.slot_exists(slot_num):
            messagebox.showwarning("ロード失敗", f"スロット {slot_num} のセーブデータが見つかりません。")
            return
        try:
            self.manager.load_game(slot_num)
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
