import sys

def run_push(time_code):
    print(f"Pushing stock report for time: {time_code}")
    # ⚠️ 這裡可接入你的分析與推播模組
    # 例如：load_data(time_code); analyze(); line_push()

if __name__ == "__main__":
    time_arg = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--time" else "undefined"
    run_push(time_arg)
