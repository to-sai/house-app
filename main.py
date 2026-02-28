import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

# --- 1. Googleスプレッドシート接続設定 ---
def connect_to_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # --- ここを修正 ---
    # ローカル（自分のPC）で動かす時はファイル、公開時はSecretsから読み込む設定
    if "gcp_service_account" in st.secrets:
        # Secretsから辞書形式で取得
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        # 自分のPCで動かす用
        creds = ServiceAccountCredentials.from_json_keyfile_name('secret_key.json', scope)
    # ------------------
    
    client = gspread.authorize(creds)
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1xW-vIAnghcRwLxm2PkejeCvLkn-d4LKB9-4CgCwooUg/edit?gid=0#gid=0"
    return client.open_by_url(SHEET_URL).sheet1

# --- 2. アプリの基本設定 ---
st.set_page_config(page_title="家事報酬管理システム", page_icon="💰")
st.title("🧽 家事お手伝い報酬管理")
st.write("家事を手伝ったら記録しよう！目標金額まであと少し？")

# 家事メニューと単価の設定（起業家として、ここを調整して利益率を考えるイメージ）
task_menu = {
    "皿洗い": 50,
    "風呂掃除": 100,
    "ゴミ出し": 30,
    "部屋の掃除": 150,
    "洗濯物たたみ": 80
}

# --- 3. 入力フォーム画面 ---
with st.form("housework_form"):
    st.subheader("お手伝いを記録する")
    
    user_name = st.text_input("名前（例：自分、妹など）")
    selected_task = st.selectbox("やった家事", list(task_menu.keys()))
    
    submit_button = st.form_submit_button("記録を送信")

    if submit_button:
        if user_name:
            try:
                # シートに接続
                sheet = connect_to_sheet()
                
                # データの準備
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                price = task_menu[selected_task]
                
                # 新しい行を追加 [日付, 内容, 金額, 名前]
                new_row = [now, selected_task, price, user_name]
                sheet.append_row(new_row)
                
                st.success(f"記録完了！{user_name}さんに {price}円 加算されました。")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
        else:
            st.warning("名前を入力してください。")

# --- 4. データの可視化（コンサル的視点） ---
st.divider()
st.subheader("📊 報酬状況の見える化")

if st.button("最新の状況を表示する"):
    try:
        sheet = connect_to_sheet()
        # 全データを取得してPandasの表（データフレーム）にする
        data = sheet.get_all_records()
        
        if data:
            df = pd.DataFrame(data)
            
            # 1. ユーザーごとの合計金額を計算
            summary = df.groupby('名前')['金額'].sum().reset_index()
            
            # 2. 合計金額を表示
            st.write("### 累計報酬額")
            for index, row in summary.iterrows():
                st.metric(label=row['名前'], value=f"{row['金額']} 円")
            
            # 3. 直近の記録を表示
            st.write("### 最近の記録（最新5件）")
            st.table(df.tail(5))
            
        else:
            st.info("まだ記録がありません。最初の記録を投稿しましょう！")
            
    except Exception as e:
        st.error(f"データ取得エラー: {e}")

# --- 5. 起業家へのヒント ---
st.sidebar.title("💡 改善のヒント")
st.sidebar.info("""
- **不正防止:** 親の承認用パスワードを付ける
- **モチベーション:** 合計金額に応じてレベルアップ機能を作る
- **分析:** どの曜日に家事が多いかグラフ化する
""")
