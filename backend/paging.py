"""Trace two page replacement policies for a single reference string."""
import argparse
import re


def compare_pages(sequence, frames):
    if type(frames) is not int or not 1 <= frames <= 8:
        raise ValueError("Choose between 1 and 8 memory frames.")
    if not isinstance(sequence, str) or len(sequence) > 512:
        raise ValueError("Enter up to 40 page numbers between 0 and 99.")
    tokens = re.split(r"[\s,]+", sequence.strip())
    if len(tokens) > 40 or any(not re.fullmatch(r"[0-9]{1,2}", item) for item in tokens):
        raise ValueError("Enter 1 to 40 page numbers (0–99), separated by spaces or commas.")
    pages = list(map(int, tokens))
    results = {}
    for policy in ("FIFO", "LRU"):
        resident = []
        order = []
        trace = []
        faults = 0
        for page in pages:
            hit = page in resident
            evicted = None
            if not hit:
                faults += 1
                if len(resident) == frames:
                    evicted = order.pop(0)
                    resident[resident.index(evicted)] = page
                else:
                    resident.append(page)
                order.append(page)
            elif policy == "LRU":
                order.remove(page)
                order.append(page)
            trace.append(dict(page=page, frames=resident.copy(), hit=hit, evicted=evicted))
        results[policy] = dict(faults=faults, hits=len(pages)-faults, trace=trace)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages", default="7 0 1 2 0 3 0 4 2 3 0 3 2")
    parser.add_argument("--frames", type=int, default=3)
    args = parser.parse_args()
    try:
        comparison = compare_pages(args.pages, args.frames)
    except ValueError as error:
        parser.error(str(error))
    print(f"Page sequence: {args.pages}\nMemory frames: {args.frames}")
    for name, result in comparison.items():
        print(f"{name}: {result['faults']} faults, {result['hits']} hits")
