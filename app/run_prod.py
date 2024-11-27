from app import app
import sys
import traceback

if __name__ == '__main__':
    try:
        print("Starting Flask application...")
        app.run(debug=False, host="0.0.0.0", port=8888, threaded=True)
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        sys.exit(1)
