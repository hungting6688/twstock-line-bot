# main.py

from modules.run_opening import analyze_opening

def main(mode):
    if mode == "opening":
        msg = analyze_opening()
        print(msg)
    else:
        print("不支援的模式")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, required=True)
    args = parser.parse_args()
    main(args.mode)
