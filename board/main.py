import argparse
from board_manager import BoardManager

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some images and heatmaps.")
    parser.add_argument("--load", type=str, help="Directory to load logs from")
    args = parser.parse_args()

    config = {
        "load": args.load,
    }

    print(config)

    board_manager = BoardManager(config)
    board_manager.init()
    board_manager.run()
    board_manager.shutdown()
