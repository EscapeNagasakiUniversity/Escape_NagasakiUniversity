# main.py
from Escape_NagasakiUniversity.class.control import GameManager

def main():
    game = GameManager()
    game.start_game()
    
    print("\n--- コマンド入力で遊ぶ脱出ゲーム（簡易テスト） ---")
    print("コマンド例: '机を調べる', '右を向く', '鍵を拾う', '鍵を使う', 'パスワード入力', '出口に行く', '終了'")
    
    while True:
        command = input("\nどうする？ > ").strip()
        
        if command == "終了":
            print("ゲームを終了します。")
            break
        elif command == "机を調べる":
            game.stage_page.object_click("机")
        elif command == "黒板を調べる":
            game.stage_page.object_click("黒板")
        elif command == "右を向く":
            game.stage_page.arrow_click("右")
        elif command == "左を向く":
            game.stage_page.arrow_click("左")
        elif command == "鍵を拾う":
            game.stage_page.item_click("小さな鍵")
        elif command == "鍵を使う":
            # 鍵を選択して机に使う流れを再現
            game.inventory_page.click_item("小さな鍵")
            game.gimmick_page.gimmick_click("desk")
        elif command == "パスワード入力":
            code = input("パスワードは？ > ")
            game.correct_create_page.submit(code)
        elif command == "出口に行く":
            game.stage_page.exit_click()
        elif command == "セーブ":
            game.savedata_manager.save_instruct()
        elif command == "ロード":
            game.savedata_manager.load_instruct()
        else:
            print("そのコマンドはわかりません。")

if __name__ == "__main__":
    main()