import os
import sys
import importlib.util

# ==============================================================================
# 変更部分:
# パスの不一致による FileNotFoundError を防ぐため、
# main.py 以下のディレクトリ構造を os.walk() で動的に検索し、
# "control.py" を自動的に見つけてインポートする関数を追加しました。
# ==============================================================================

def get_game_manager():
    """
    現在のディレクトリ以下から 'control.py' を自動検索し、
    動的にインポートして GameManager クラスを返す関数です。
    """
    # main.pyが存在するディレクトリの絶対パスを取得
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_path = None

    # base_dir 以下のすべてのフォルダとファイルを再帰的に検索
    for root, dirs, files in os.walk(base_dir):
        # 検索対象のファイル名が見つかった場合
        if "control.py" in files:
            # 親フォルダが "class" であるものを最優先のターゲットとする
            if os.path.basename(root) == "class":
                target_path = os.path.join(root, "control.py")
                break
            # それ以外の場合でも、とりあえず候補として保持しておく
            elif target_path is None:
                target_path = os.path.join(root, "control.py")

    # 対象ファイルがどこにも見つからなかった場合はエラーを発生させて終了
    if target_path is None:
        raise FileNotFoundError("control.py が現在のフォルダ以下に見つかりませんでした。必要なファイルが揃っているか確認してください。")

    print(f"-> 【システム】モジュールを発見しました: {target_path}")

    # ファイルパスからモジュールの仕様（Spec）を作成
    spec = importlib.util.spec_from_file_location("control_module", target_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"モジュールの仕様を作成できませんでした: {target_path}")

    # 仕様を基に実際のモジュールオブジェクトを作成
    control_module = importlib.util.module_from_spec(spec)
    
    # モジュールを sys.modules に登録（他の依存関係でバグを起こさないための安全策）
    sys.modules["control_module"] = control_module
    
    # スクリプトを実行して中身をロードする
    spec.loader.exec_module(control_module)
    
    # ロードしたモジュールから GameManager クラスを抽出して返す
    return control_module.GameManager

# ==============================================================================
# モジュールの読み込み実行部
# ==============================================================================
try:
    # 検索機能を利用して GameManager を動的に取得
    GameManager = get_game_manager()
except Exception as e:
    # 検索やインポートに失敗した場合のエラー処理
    print(f"【インポートエラー】モジュールの読み込みに失敗しました。\n詳細: {e}")
    sys.exit(1)


def main():
    """
    ゲームのメインループを実行する関数です。
    """
    try:
        # ゲーム全体の進行や各画面のインスタンスを統括するマネージャーを生成
        game = GameManager()
        # ゲームの初期化、または最初のステージの読み込み処理を実行
        game.start_game()
    except Exception as e:
        # GameManagerの初期化時における予期せぬエラーをキャッチ
        print(f"【初期化エラー】ゲームの開始に失敗しました。\n詳細: {e}")
        return
    
    # ユーザーに対して操作可能なコマンドの案内を表示
    print("\n--- コマンド入力で遊ぶ脱出ゲーム（簡易テスト） ---")
    print("コマンド例: '机を調べる', '黒板を調べる', '右を向く', '左を向く', '鍵を拾う', '鍵を使う', 'パスワード入力', '出口に行く', 'セーブ', 'ロード', '終了'")
    
    # メインのゲームループ。ユーザーが「終了」を選ぶまで継続
    while True:
        try:
            # ユーザーからのコマンド入力を受け付け、前後の余分な空白を削除
            command = input("\nどうする？ > ").strip()
            
            # --- 1. ゲームの終了処理 ---
            if command == "終了":
                print("ゲームを終了します。")
                break
                
            # --- 2. ステージ内のオブジェクト調査 ---
            elif command == "机を調べる":
                print("-> 机を調べています...")
                game.stage_page.object_click("机")
                
            elif command == "黒板を調べる":
                print("-> 黒板を調べています...")
                game.stage_page.object_click("黒板")
                
            # --- 3. 視点変更（方向転換） ---
            elif command == "右を向く":
                print("-> 右を向きました。")
                game.stage_page.arrow_click("右")
                
            elif command == "左を向く":
                print("-> 左を向きました。")
                game.stage_page.arrow_click("左")
                
            # --- 4. アイテムの取得 ---
            elif command == "鍵を拾う":
                print("-> 足元の小さな鍵に手を伸ばします...")
                game.stage_page.item_click("小さな鍵")
                
            # --- 5. アイテムの使用 ---
            elif command == "鍵を使う":
                print("-> インベントリから「小さな鍵」を選択し、机の引き出しに試します...")
                # インベントリ画面で鍵を選択状態にする
                game.inventory_page.click_item("小さな鍵")
                # ギミック画面に対して、選択中のアイテム（鍵）を机（desk）に使用する
                game.gimmick_page.gimmick_click("desk")
                
            # --- 6. パスワード・暗号入力 ---
            elif command == "パスワード入力":
                code = input("パスワードは？ > ").strip()
                print(f"-> パスワード「{code}」を入力中...")
                # 答え合わせ・ギミック解除画面へコードを送信
                game.correct_create_page.submit(code)
                
            # --- 7. 脱出・出口への移動 ---
            elif command == "出口に行く":
                print("-> 出口の扉へ向かいます...")
                game.stage_page.exit_click()
                
            # --- 8. データ管理（セーブ＆ロード） ---
            elif command == "セーブ":
                print("-> ゲームデータを保存します...")
                game.savedata_manager.save_instruct()
                
            elif command == "ロード":
                print("-> 前回のセーブデータを読み込みます...")
                game.savedata_manager.load_instruct()
                
            # --- 9. 無効なコマンドの処理 ---
            else:
                print("そのコマンドはわかりません。正しいコマンドを入力してください。")
                
        except AttributeError as e:
            # GameManager内の各ページやメソッドが存在しない場合の致命的エラーをキャッチ
            print(f"【システムエラー】ゲームオブジェクトの呼び出しに失敗しました: {e}")
        except Exception as e:
            # その他の予期せぬエラー（実行中の不具合など）が発生した場合のセーフティネット
            print(f"【予期せぬエラー】エラーが発生しました: {e}")

if __name__ == "__main__":
    # スクリプトが直接実行された場合のみメイン関数を起動
    main()