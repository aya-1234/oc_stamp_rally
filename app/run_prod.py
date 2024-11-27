from app import app
import sys
import traceback
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

if __name__ == '__main__':
    
    # import os
    
    # # data.dbファイルのパスを設定
    # db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance", "data.db")
    
    # # ファイルが存在する場合は削除
    # if os.path.exists(db_path):
    #     try:
    #         os.remove(db_path)
    #         logging.info("Existing data.db file was removed")
    #     except Exception as e:
    #         logging.error(f"Error removing data.db: {str(e)}")



    try:
        logging.info("Starting Flask application...")
        app.run(debug=False, host="0.0.0.0", port=8888, threaded=True)
    except Exception as e:
        logging.error(f"Error starting application: {str(e)}")
        logging.error("Traceback:")
        traceback.print_exc()
        sys.exit(1)
