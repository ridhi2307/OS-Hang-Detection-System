
from collections import defaultdict


def build_wait_for_graph(processes, allocations, requests):

    graph = defaultdict(list)

    # Add all processes as graph nodes
    for process in processes:
        graph[process] = []

    # If P1 requests a resource held by P2,
    # P1 must wait for P2.
    for waiting_process, requested_resource in requests.items():

        for holding_process, held_resource in allocations.items():

            if requested_resource == held_resource:

                graph[waiting_process].append(holding_process)

    return graph


def detect_cycle(graph):

    visited = set()
    recursion_stack = set()

    def dfs(process):

        visited.add(process)
        recursion_stack.add(process)

        for neighbor in graph[process]:

            if neighbor not in visited:

                if dfs(neighbor):
                    return True

            elif neighbor in recursion_stack:

                return True

        recursion_stack.remove(process)

        return False

    for process in graph:

        if process not in visited:

            if dfs(process):
                return True

    return False


def display_deadlock_report(graph, deadlock_detected):

    print("\n" + "=" * 65)
    print("                 DEADLOCK DETECTION REPORT")
    print("=" * 65)

    print("\nWAIT-FOR GRAPH:")

    for process, dependencies in graph.items():

        if dependencies:
            print(f"{process} ---> {', '.join(dependencies)}")
        else:
            print(f"{process} ---> No dependency")

    print("\n" + "-" * 65)

    if deadlock_detected:

        print("WARNING: DEADLOCK DETECTED!")
        print("A cycle exists in the wait-for graph.")

    else:

        print("No deadlock detected.")
        print("The wait-for graph contains no cycle.")

    print("=" * 65)


def run_deadlock_detection():

    # Simulated processes
    processes = ["P1", "P2", "P3"]

    # Resource allocation:
    # P1 holds R1
    # P2 holds R2
    # P3 holds R3
    allocations = {
        "P1": "R1",
        "P2": "R2",
        "P3": "R3"
    }

    # Resource requests:
    # P1 waits for R2 (held by P2)
    # P2 waits for R3 (held by P3)
    # P3 waits for R1 (held by P1)
    requests = {
        "P1": "R2",
        "P2": "R3",
        "P3": "R1"
    }

    graph = build_wait_for_graph(
        processes,
        allocations,
        requests
    )

    deadlock_detected = detect_cycle(graph)

    display_deadlock_report(graph, deadlock_detected)


if __name__ == "__main__":

    print("Starting deadlock detection...")

    run_deadlock_detection()
