import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import pytz

# --- 1. Googleスプレッドシート接続設定 ---
@st.cache_resource  #キャッシュ化
def connect_to_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

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

# --- 修正点2：データの読み込みを関数にしてキャッシュする ---
@st.cache_data(ttl=60)  # 60秒間はデータを保存（キャッシュ）して高速化する
def get_all_data():
    sheet = connect_to_sheet()
    return sheet.get_all_records()

# --- 2. アプリの基本設定 ---
st.set_page_config(page_title="手伝い記録", page_icon="💹")
st.title("手伝い記録管理システム")
# 「st.write(" ")」で文章を追加可能

# 家事メニューと単価の設定（起業家として、ここを調整して利益率を考えるイメージ）
task_name = {
    "ゆうたろう": "ゆうたろう",
     "ひろき": "ひろき",
}
   
task_menu = {
    "皿洗い": 100,
    "風呂掃除": 100,
    "洗濯物（服）": 50,
    "洗濯物（タオル）": 10,
    "布団たたみ": 10
}

# --- 3. 入力フォーム画面 ---
with st.form("housework_form"):
    st.subheader("お手伝いを記録する")
    
    user_name = st.selectbox("名前", list(task_name.keys()))
    selected_task = st.selectbox("やった家事", list(task_menu.keys()))
    
    submit_button = st.form_submit_button("記録を送信")

    if submit_button:
        if user_name:
            try:
                # シートに接続
                sheet = connect_to_sheet()
                
                # データの準備
                # 日本のタイムゾーンを指定して現在時刻を取得
                tokyo_tz = pytz.timezone('Asia/Tokyo')
                now = datetime.now(tokyo_tz).strftime("%Y-%m-%d %H:%M:%S")
                price = task_menu[selected_task]
                
                # 新しい行を追加 [日付, 内容, 金額, 名前]
                new_row = [now, selected_task, price, user_name]
                sheet.append_row([now, selected_task, task_menu[selected_task], user_name])
                
                st.success(f"記録完了！{user_name}さんに {price}円 加算されました。")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
        else:
            st.warning("名前を入力してください。")

# --- 4. データの可視化（コンサル的視点） ---
#st.divider()
#st.subheader("報酬状況")

#--- 4. 報酬の集計表示（月次レポート機能付き） ---

st.divider()
if st.button("最新の報酬状況を表示"):
    try:
        # キャッシュされた関数からデータを取得
        data = get_all_data() 
        if data:
            df = pd.DataFrame(data)
            
            # 【重要】日付列を日付型に変換し、新しい「月」列を作る
            # 日付列の名前が「日時」や「日付」など、シートの1行目と一致しているか確認してください
            date_column = '日時' # ここをシートの1行目の名前に合わせる
            df[date_column] = pd.to_datetime(df[date_column])
            df['月'] = df[date_column].dt.strftime('%Y-%m')
            
            # --- セクションA：全体の累計合計 ---
            st.write("### 💰 全期間の累計報酬")
            summary = df.groupby('名前')['金額'].sum().reset_index()
            cols = st.columns(len(summary))
            for i, row in summary.iterrows():
                cols[i].metric(label=row['名前'], value=f"{row['金額']} 円")
            
            # --- セクションB：月ごとの集計（ここが新規追加！） ---
            st.write("### 📅 月ごとの報酬まとめ")
            # ピボットテーブルという機能を使って、横軸に名前、縦軸に月を並べます
            monthly_pivot = df.pivot_table(
                index='月', 
                columns='名前', 
                values='金額', 
                aggfunc='sum', 
                fill_value=0
            ).sort_index(ascending=False) # 最新の月を一番上に
            
            # 表として表示
            st.dataframe(monthly_pivot, use_container_width=True)
            
            # 視覚的に分かりやすくグラフも追加（オプション）
            st.bar_chart(monthly_pivot)

            st.write("### 📝 直近5件の履歴")
            st.table(df.tail(5))
            
        else:
            st.info("まだデータがありません。")
    except Exception as e:
        st.error(f"分析エラーが発生しました: {e}")
# --- 修正後の表示部分 ---
if st.button("最新の報酬状況を表示する"):
    try:
        # sheet.get_all_records() の代わりに、キャッシュ付きの関数を呼ぶ
        data = get_all_data() 
        if data:
            # (以下、これまでの集計処理と同じ)
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
            st.info("まだ記録がありません")
            
    except Exception as e:
        st.error(f"データ取得エラー: {e}")

# --- サイドバーの編集 ---
# st.sidebar.title("💡 改善のヒント")
# st.sidebar.info("""
# - **不正防止:** 親の承認用パスワードを付ける
# - **モチベーション:** 合計金額に応じてレベルアップ機能を作る
# - **分析:** どの曜日に家事が多いかグラフ化する
# """)
