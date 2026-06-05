import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Semantic UML Diff")
    parser.add_argument("--base", required=True, help="Base UML directory")
    parser.add_argument("--pr", required=True, help="PR UML directory")
    parser.add_argument("--token", required=False, help="GitHub Token")

    args = parser.parse_args()

    print("Starting Semantic UML Diff")
    print(f"Base dir: {args.base}")
    print(f"PR dir: {args.pr}")

    # TODO: Implement pipeline here
    print("Pipeline completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
